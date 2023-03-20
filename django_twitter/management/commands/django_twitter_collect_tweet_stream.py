from __future__ import print_function
import django
import tweepy
import json
import datetime

from django import db
from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django_pewtils import reset_django_connection, reset_django_connection_wrapper
from multiprocessing import Pool
from pewhooks.twitter import TwitterAPIHandler

from django_twitter.utils import safe_get_or_create


allowable_limit_types = {
    "minute": ["m", "min", "minutes", "minute"],
    "hour": ["h", "hour", "hours"],
    "day": ["d", "days", "day"],
    "tweet": ["t", "tweets"],
}


class Command(BaseCommand):
    """
    Download a stream of tweets using the Twitter streaming API, either randomly sampling or pulling a \
    sample of tweets that match to a specific `keyword_query`. Django Twitter will use multiprocessing to \
    make sure it keeps up with the incoming volume of tweets. The data collection processes uses a queue \
    to fill up batches of `queue_size` tweets, and once full it then sends each batch to a dedicated process \
    that saves the tweets to the database.

    :param num_cores: (Optional) Number of cores to use for processes that save the tweets to the database (default 2)
    :param queue_size: (Optional) Size of the batches of tweets that will be sent to each data-saving proceess (default 500)
    :param keyword_query: (Optional) Query to use to filter tweets in the stream
    :param test: Use when testing to avoid resetting DB connections

    :param add_to_profile_set: (Optional) The name of a profile set to add all encountered profiles to. Can be \
    any arbitrary string you want to use; if the profile set doesn't already exist, it will be created
    :param add_to_tweet_set: (Optional) The name of a tweet set to add each tweet to. Can be \
    any arbitrary string you want to use; if the tweet set doesn't already exist, it will be created.

    :param api_key: (Optional) Twitter API key, if you don't have the TWITTER_API_KEY environment variable set
    :param api_secret: (Optional) Twitter API secret, if you don't have the TWITTER_API_SECRET environment variable set
    :param access_token: (Optional) Twitter access token, if you don't have the TWITTER_API_ACCESS_TOKEN environment \
    variable set
    :param api_secret: (Optional) Twitter API access secret, if you don't have the TWITTER_API_ACCESS_SECRET \
    environment variable set
    """

    def add_arguments(self, parser):

        parser.add_argument("--num_cores", type=int, default=2)
        parser.add_argument("--queue_size", type=int, default=500)
        parser.add_argument("--keyword_query", type=str)
        parser.add_argument(
            "--limit",
            type=str,
            default="",
            help="Accepts: x tweets, x minutes, x hours, x days",
        )
        parser.add_argument("--test", action="store_true", default=False)

        parser.add_argument("--add_to_tweet_set", type=str)
        parser.add_argument("--add_to_profile_set", type=str)

        parser.add_argument("--api_key", type=str)
        parser.add_argument("--api_secret", type=str)
        parser.add_argument("--access_token", type=str)
        parser.add_argument("--access_secret", type=str)

    def handle(self, *args, **options):

        self.twitter = TwitterAPIHandler(
            api_key=options["api_key"],
            api_secret=options["api_secret"],
            access_token=options["access_token"],
            access_secret=options["access_secret"],
        )

        # determine time / tweets
        self.limit = {}
        if options["limit"] == "":
            # could technically put these above but want to make it more explicit
            self.limit["limit_type"] = None
            self.limit["limit_count"] = None
            self.limit["limit_time"] = None
        else:
            limit_values = options["limit"].split(" ")

            # error checking
            if not len(limit_values) == 2:
                raise ValueError(
                    "Please specify limit in format: <number> <duration/tweets>."
                )
            try:
                int(limit_values[0])
            except ValueError:
                raise ValueError("Please specify a number of minutes/days/hours/tweets")

            passed_allowed_limit_type = False
            for limit_type in list(allowable_limit_types.keys()):
                if limit_values[1] in allowable_limit_types[limit_type]:
                    self.limit["limit_type"] = limit_type
                    passed_allowed_limit_type = True
                    break
            if not passed_allowed_limit_type:
                raise ValueError("Please specify limit in appropriate duration.")

            if limit_values[1] in allowable_limit_types["tweet"]:
                self.limit["limit_count"] = int(limit_values[0])
            elif limit_values[1] in allowable_limit_types["minute"]:
                self.limit["limit_time"] = datetime.datetime.now() + datetime.timedelta(
                    minutes=int(limit_values[0])
                )
            elif limit_values[1] in allowable_limit_types["hour"]:
                self.limit["limit_time"] = datetime.datetime.now() + datetime.timedelta(
                    hours=int(limit_values[0])
                )
            elif limit_values[1] in allowable_limit_types["day"]:
                self.limit["limit_time"] = datetime.datetime.now() + datetime.timedelta(
                    days=int(limit_values[0])
                )
            else:
                raise ValueError("Could not set limit")

        auth = self.twitter._get_auth()
        stream = Stream(
            auth.consumer_key,
            auth.consumer_secret,
            auth.access_token,
            auth.access_token_secret,
            tweet_set=options["add_to_tweet_set"],
            profile_set=options["add_to_profile_set"],
            num_cores=options["num_cores"],
            queue_size=options["queue_size"],
            limit=self.limit,
            test=options["test"],
        )

        self.twitter.capture_stream_sample(
            stream,
            use_async=False,
            keywords=[options["keyword_query"]] if options["keyword_query"] else None,
        )


class Stream(tweepy.Stream):
    def __init__(
        self,
        *args,
        tweet_set=None,
        profile_set=None,
        num_cores=2,
        queue_size=500,
        limit=None,
        test=False,
        **kwargs,
    ):

        self.tweet_set = tweet_set
        self.profile_set = profile_set
        self.queue_size = queue_size
        self.limit = limit if limit else {"limit_type": None}
        self.test = test

        self.tweet_queue = []
        self.pool = Pool(processes=num_cores)
        self.num_cores = num_cores
        self.scanned_counter = 0
        self.processed_counter = 0

        super(Stream, self).__init__(*args, **kwargs)
        print("Stream initialized")

    def on_data(self, data):

        try:
            data = json.loads(data)

            if "delete" in data:
                delete = data["delete"]["status"]
                return self.on_delete(delete["id"], delete["user_id"])
            elif "disconnect" in data:
                return self.on_disconnect_message(data["disconnect"])
            elif "limit" in data:
                return self.on_limit(data["limit"]["track"])
            elif "scrub_geo" in data:
                return self.on_scrub_geo(data["scrub_geo"])
            elif "status_withheld" in data:
                return self.on_status_withheld(data["status_withheld"])
            elif "user_withheld" in data:
                return self.on_user_withheld(data["user_withheld"])
            elif "warning" in data:
                return self.on_warning(data["warning"])
            else:

                self.scanned_counter += 1
                self.tweet_queue.append(data)
                if len(self.tweet_queue) >= self.queue_size:

                    if self.num_cores > 1:
                        self.pool.apply_async(
                            save_tweets,
                            args=[
                                list(self.tweet_queue),
                                self.tweet_set,
                                self.profile_set,
                                self.test,
                            ],
                        )
                    else:
                        save_tweets(
                            list(self.tweet_queue),
                            self.tweet_set,
                            self.profile_set,
                            self.test,
                        )
                        # TODO: Latest version of Django is causing errors with multiprocessing; need to fix
                        # self.pool.apply(
                        #     save_tweets,
                        #     args=[
                        #         list(self.tweet_queue),
                        #         self.tweet_set,
                        #         self.profile_set,
                        #         self.test,
                        #     ],
                        # )

                    self.tweet_queue = []
                    self.processed_counter += self.queue_size
                    print(
                        "{} tweets scanned, {} sent for processing".format(
                            self.scanned_counter, self.processed_counter
                        )
                    )
                    if self.limit_exceeded():
                        # wait for db connections
                        try:
                            self.pool.close()
                        except Exception as e:
                            print("WOMP: {}".format(e))
                        try:
                            self.pool.join()
                        except Exception as e:
                            print("WOMPIER: {}".format(e))
                        if not self.test:
                            db.connections.close_all()
                        self.disconnect()
                        return False
                    else:
                        return True
                else:
                    return True

        except Exception as e:

            print("UNKNOWN ERROR: {}".format(e))
            import pdb

            pdb.set_trace()

            return True

    def limit_exceeded(self):
        if self.limit["limit_type"] is None:
            return True
        elif self.limit["limit_type"] == "tweet":
            return self.processed_counter >= self.limit["limit_count"]
        else:
            return datetime.datetime.now() >= self.limit["limit_time"]


def save_tweets(tweets, tweet_set, profile_set, test):

    if not test:
        reset_django_connection(settings.TWITTER_APP)

    if tweet_set:
        tweet_set = safe_get_or_create(
            "AbstractTweetSet", "name", tweet_set, create=True
        )
    if profile_set:
        profile_set = safe_get_or_create(
            "AbstractTwitterProfileSet", "name", profile_set, create=True
        )

    success, error = 0, 0
    for tweet_json in tweets:
        try:
            tweet = safe_get_or_create(
                "AbstractTweet", "twitter_id", tweet_json["id_str"], create=True
            )
            tweet.update_from_json(tweet_json)
            if tweet_set:
                tweet_set.tweets.add(tweet)
            if profile_set:
                profile_set.profiles.add(tweet.profile)
            success += 1
        except django.db.utils.IntegrityError:
            error += 1

    print("{} tweets saved, {} errored".format(success, error))
    return True
