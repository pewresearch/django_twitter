from __future__ import print_function
from builtins import str
import os, glob
import json
import random

from django.conf import settings
from django.core.management.base import BaseCommand
from django.apps import apps
from django import db
from django.db.utils import IntegrityError
from multiprocessing import Pool
from tqdm import tqdm

from django_pewtils import reset_django_connection, reset_django_connection_wrapper


class Command(BaseCommand):
    def add_arguments(self, parser):

        parser.add_argument("-f", "--folder_name", type=str)
        parser.add_argument("--tweet_set", type=str)
        parser.add_argument("--num_cores", type=int, default=2)
        parser.add_argument("--queue_size", type=int, default=500)
        parser.add_argument("--profile_set", type=str)
        parser.add_argument("--sample_rate", type=float, default=1.0)
        parser.add_argument("--limit", type=int)

    def handle(self, *args, **options):

        self.queue_size = options["queue_size"]

        self.tweet_queue = []
        self.num_cores = options["num_cores"]
        self.pool = Pool(processes=self.num_cores)

        self.tweet_set = None
        if options["tweet_set"]:
            tweet_set_model = apps.get_model(
                app_label=settings.TWITTER_APP, model_name=settings.TWEET_SET_MODEL
            )
            self.tweet_set, created = tweet_set_model.objects.get_or_create(
                name=options["tweet_set"]
            )

        self.profile_set = None
        if options["profile_set"]:
            self.profile_set = options["profile_set"]

        # and run through the tweets
        self.scanned_counter = 0
        self.processed_counter = 0
        tweet_queue = []
        for tweet_payload in generate_tweets(options["folder_name"]):

            if random.random() < options["sample_rate"]:

                t = load_tweet(tweet_payload)
                if t:
                    self.tweet_queue.append(t)
                self.scanned_counter += 1

                if len(self.tweet_queue) >= self.queue_size:
                    print("saving..")

                    if self.num_cores > 1:
                        self.pool.apply_async(save_users, args=[list(self.tweet_queue)])
                        self.pool.apply_async(
                            save_tweets,
                            args=[
                                list(tweet_queue),
                                self.tweet_set.pk if self.tweet_set else None,
                            ],
                        )
                        self.pool.apply_async(
                            save_profileset, args=[list(tweet_queue), self.profile_set]
                        )
                    else:
                        self.pool.apply(save_users, args=[list(self.tweet_queue)])
                        self.pool.apply(
                            save_tweets,
                            args=[
                                list(self.tweet_queue),
                                self.tweet_set.pk if self.tweet_set else None,
                            ],
                        )
                        self.pool.apply(
                            save_profileset,
                            args=[list(self.tweet_queue), self.profile_set],
                        )
                        # save_tweets(list(self.tweet_queue),
                        #             self.tweet_set.pk if self.tweet_set else None)
                        # save_profileset(list(self.tweet_queue), self.profile_set)
                    self.tweet_queue = []
                    self.processed_counter += self.queue_size
                    print(
                        "{} tweets scanned, {} sent for processing".format(
                            self.scanned_counter, self.processed_counter
                        )
                    )

        # In case there's still remaining tweets in the queue
        save_all(
            tweet_queue, self.profile_set, self.tweet_set.pk if self.tweet_set else None
        )

        self.pool.close()
        self.pool.join()
        db.connections.close_all()


def save_all(tweet_queue, profile_set, tweet_set_pk=None):

    save_tweets(tweet_queue, tweet_set_pk)
    save_users(tweet_queue)
    save_profileset(tweet_queue, profile_set)


def generate_tweet_files(folder_name):

    # Raise exception if folder doesn't exist
    if not os.path.isdir(folder_name):
        raise ValueError("Directory not found.")

    for file in glob.glob(os.path.join(folder_name, "*.json")):
        yield file


def generate_tweets(folder_name):
    """
    Generator for tweets from GNIP - since this could get run
     multiple times
    :return: JSON payload of tweet
    """

    for file in generate_tweet_files(folder_name):

        # read each file in as a list of strings, one JSON/tweet per line
        with (open(file, "r")) as f:
            print("opening {}".format(f))
            tweets = f.readlines()
        # process each JSON, extracting the ID and URLs;
        # since it's a string, omit the final two characters
        for tweet in tweets:
            yield json.loads(tweet[0:-2])


def load_tweet_file(file, options, kwquery=None):

    with (open(file, "r")) as f:
        for tweet in tqdm(f, desc="Loading tweets from file '{}'".format(file)):
            tweet_payload = json.loads(tweet[0:-2])
            load_tweet(tweet_payload, options, kwquery=kwquery)


def get_body_text(payload):
    """
    Retrieves text as it appears. If it is a retweet, returns original text, without RT.
    Does not include quoted text unless called with the quoted text payload
    :param payload: json object of tweet or quoted tweet
    :return: string of text
    """
    # check if it's a retweet
    text = u"{}".format(payload["body"])
    # curr_tweet_text_match = rt_match.match(text)
    if payload.get("object", {}).get("body"):
        text = u"{}".format(payload["object"]["body"])

    # Now check if there's a longer version and if so automatically add that
    if payload["object"].get("long_object"):
        # still checking retweet here
        text = u"{}".format(payload["object"]["long_object"]["body"])
    return text


def extract_data(payload):
    tweet_data = {}
    tweet_data["twitter_id"] = payload["id"].split(":")[-1]
    tweet_data["id_str"] = str(tweet_data["twitter_id"])
    # User
    profile_data = payload["actor"]
    tweet_data["user"] = {}
    tweet_data["user"]["twitter_id"] = profile_data["id"].split(":")[-1]
    tweet_data["user"]["id"] = tweet_data["user"]["twitter_id"]
    tweet_data["user"]["id_str"] = str(tweet_data["user"]["twitter_id"])
    tweet_data["user"]["created_at"] = profile_data["postedTime"]
    tweet_data["user"]["screen_name"] = profile_data["preferredUsername"].lower()
    tweet_data["user"]["description"] = profile_data["summary"]
    tweet_data["user"]["favorites_count"] = profile_data["favoritesCount"]
    tweet_data["user"]["followers_count"] = profile_data["followersCount"]
    tweet_data["user"]["friends_count"] = profile_data["friendsCount"]
    tweet_data["user"]["listed_count"] = profile_data["listedCount"]
    tweet_data["user"]["lang"] = profile_data["languages"][0]
    tweet_data["user"]["statuses_count"] = profile_data["statusesCount"]
    tweet_data["user"]["profile_image_url"] = profile_data["image"]
    tweet_data["user"]["verified"] = profile_data["verified"]
    tweet_data["user"]["contributors_enabled"] = None
    tweet_data["user"]["entities"] = {}
    tweet_data["user"]["entities"]["urls"] = []
    for link in profile_data["links"]:
        if link["href"]:
            tweet_data["user"]["entities"]["urls"].append(
                {"expanded_url": link["href"]}
            )
    tweet_data["user"]["verified"] = profile_data["verified"]

    # Tweet
    tweet_data["twitter_id"] = payload["id"].split(":")[-1]
    tweet_data["created_at"] = payload["postedTime"]
    tweet_data["retweet_count"] = payload.get("retweetCount", 0)
    tweet_data["favorite_count"] = payload["favoritesCount"]
    tweet_data["lang"] = payload["twitter_lang"]
    tweet_data["text"] = get_body_text(payload)

    # tweet urls, hashtags, and mentions are all in twitter_entities
    # Unclear if that includes anything that's in a retweet, but ok for now
    tweet_data["entities"] = payload.get("twitter_entities", {})

    return tweet_data


def load_tweet(tweet_payload):

    # There's always an information summary tweet, which we want to skip
    try:
        if tweet_payload.get("id"):
            # Get tweet data
            tweet_data = extract_data(tweet_payload)
            # Matching quotes, replys, retweets
            if tweet_payload.get("inReplyTo", ""):
                tweet_data["in_reply_to_status_id"] = tweet_payload["inReplyTo"][
                    "link"
                ].split("/")[-1]
                tweet_data["in_reply_to_status_id_str"] = tweet_data[
                    "in_reply_to_status_id"
                ]
                tweet_data["in_reply_to_user_id_str"] = tweet_payload["inReplyTo"][
                    "link"
                ].split("/")[-3]
            if tweet_payload.get("verb", "") == "share":  # this is a retweet
                tweet_data["retweeted_status"] = extract_data(tweet_payload["object"])
            if tweet_payload.get("twitter_quoted_status", {}):
                tweet_data["quoted_status"] = extract_data(
                    tweet_payload["twitter_quoted_status"]
                )

            return tweet_data
        else:
            return None
    except Exception as e:
        print(e)


def save_tweets(tweets, tweet_set_id):

    reset_django_connection(settings.TWITTER_APP)

    tweet_model = apps.get_model(
        app_label=settings.TWITTER_APP, model_name=settings.TWEET_MODEL
    )
    tweet_set = None
    if tweet_set_id:
        tweet_set_model = apps.get_model(
            app_label=settings.TWITTER_APP, model_name=settings.TWEET_SET_MODEL
        )
        tweet_set = tweet_set_model.objects.get(pk=tweet_set_id)
    success, error = 0, 0
    for tweet_json in tweets:
        try:
            tweet, created = tweet_model.objects.get_or_create(
                twitter_id=tweet_json["id_str"]
            )
            tweet.update_from_json(tweet_json)
            if tweet_set:
                tweet_set.tweets.add(tweet)
            success += 1
        except IntegrityError:
            error += 1

    print("{} tweets saved, {} errored".format(success, error))
    return True


def save_users(tweets):

    reset_django_connection(settings.TWITTER_APP)

    tweet_model = apps.get_model(
        app_label=settings.TWITTER_APP, model_name=settings.TWEET_MODEL
    )
    success, error = 0, 0
    for tweet_json in tweets:
        try:
            tweet, created = tweet_model.objects.get_or_create(
                twitter_id=tweet_json["id_str"]
            )
            tweet.update_from_json(tweet_json)
            success += 1
        # except IntegrityError:
        #     error += 1
        except:
            print(tweet_json)
            import pdb

            pdb.set_trace()

    print("{} users saved, {} errored".format(success, error))


all_users = set()


def save_profileset(tweets, profile_set_id):

    reset_django_connection(settings.TWITTER_APP)

    user_model = apps.get_model(
        app_label=settings.TWITTER_APP, model_name=settings.TWITTER_PROFILE_MODEL
    )
    profile_set = None
    if profile_set_id:
        profile_set_model = apps.get_model(
            app_label=settings.TWITTER_APP,
            model_name=settings.TWITTER_PROFILE_SET_MODEL,
        )
        profile_set, created = profile_set_model.objects.get_or_create(
            name=profile_set_id
        )
    success, error, create_count = 0, 0, 0
    for tweet_json in tweets:
        user = tweet_json["user"]["id"]
        if user not in all_users:
            all_users.add(user)
            twitter_user, created = user_model.objects.get_or_create(twitter_id=user)
            if created:
                create_count += 1
            if profile_set:
                profile_set.profiles.add(twitter_user)
            success += 1
    print(
        "{} profiles set, {} errored, {} created".format(success, error, create_count)
    )
