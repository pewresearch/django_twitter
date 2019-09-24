from __future__ import print_function
from multiprocessing import Pool

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db.utils import IntegrityError

from dippybird.models import Tweet, Link, KeywordQuery
from pewtils import decode_text
from django_pewtils import reset_django_connection, consolidate_objects

import os, json, glob, re
from tqdm import tqdm


class Command(BaseCommand):
    def add_arguments(self, parser):

        parser.add_argument("-f", "--folder_name", type=str)
        parser.add_argument("-b", "--batch_id", type=int)
        parser.add_argument("-k", "--keyword", type=str)
        parser.add_argument("-l", "--limit", type=int, default=-1)
        parser.add_argument("--num_cores", type=int, default=1)
        parser.add_argument("--use_multiprocessing", action="store_true", default=False)
        parser.add_argument(
            "--extract_secondary_links", action="store_true", default=False
        )

    def handle(self, *args, **options):

        # set retweet pattern
        rt_match = re.compile(r"RT @.*: (.*)")

        if options["use_multiprocessing"]:
            pool = Pool(processes=options["num_cores"])
            for file in generate_tweet_files(options["folder_name"]):
                if options["num_cores"] == 1:
                    pool.apply(
                        load_tweet_file,
                        [file, rt_match, options],
                        {"kwquery": options["keyword"]},
                    )
                else:
                    pool.apply_async(
                        load_tweet_file,
                        [file, rt_match, options],
                        {"kwquery": options["keyword"]},
                    )
            pool.close()
            pool.join()

        else:

            # tweet generator
            tweets = generate_tweets(options["folder_name"])
            count = 0

            if options["keyword"]:
                # keyword query
                kwquery = KeywordQuery.objects.get(name=options["keyword"])

            # and run through the tweets
            for tweet_payload in tqdm(tweets, desc="Loading GNIP"):
                # for debugging or just doing a certain chunk
                if options["limit"] > 0:
                    if count == options["limit"]:
                        break
                    else:
                        count += 1
                load_tweet(tweet_payload, rt_match, options, kwquery=kwquery)


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
            tweets = f.readlines()
        # process each JSON, extracting the ID and URLs;
        # since it's a string, omit the final two characters
        for tweet in tweets:
            yield json.loads(tweet[0:-2])


def load_tweet_file(file, rt_match, options, kwquery=None):

    reset_django_connection("dippybird")

    if kwquery:
        # keyword query
        kwquery = KeywordQuery.objects.get(name=kwquery)

    with (open(file, "r")) as f:
        for tweet in tqdm(f, desc="Loading tweets from file '{}'".format(file)):
            tweet_payload = json.loads(tweet[0:-2])
            load_tweet(tweet_payload, rt_match, options, kwquery=kwquery)


# def get_body_text(payload, rt_match):
#     '''
#     Retrieves text as it appears. If it is a retweet, returns original text, without RT.
#     Does not include quoted text unless called with the quoted text payload
#     :param payload: json object of tweet or quoted tweet
#     :return: string of text
#     '''
#     # check if it's a retweet
#     text = u"{}".format(payload['body'])
#     curr_tweet_text_match = rt_match.match(text)
#     if curr_tweet_text_match and payload.get('object', {}).get('body'):
#         text = u"{}".format(payload['object']['body'])
#
#     # Now check if there's a longer version and if so automatically add that
#     if payload['object'].get('long_object'):
#         # still checking retweet here
#         text = u"{}".format(payload['object']['long_object']['body'])
#     return text


# def get_full_text(tweet_payload, tweet, rt_match):
#     '''
#     Returns full text as it would appear on the screen, including any links and descriptions
#     :param tweet_payload: JSON of tweet from GNIP
#     :return: full text, including links
#     '''
#     # start with current text
#     text = tweet.text
#
#     # extract text from a quoted tweet
#     if tweet_payload.get('twitter_quoted_status'):
#         text += u"\n{}".format(get_body_text(tweet_payload['twitter_quoted_status'], rt_match))
#
#     # if tweet_payload.get('gnip') and tweet_payload['gnip'].get('urls'):
#     #     for url_object in tweet_payload['gnip']['urls']:
#     #         if url_object.get('expanded_url'):
#     #             url = url_object['expanded_url']
#     #             url_title = url_object['expanded_url_title']
#     #             url_desc = url_object['expanded_url_description']
#     #             text += u"\n{}\n{}\n{}".format(url, url_title, url_desc)
#     #         else:
#     #             text += u"\n{}".format(url_object['url'])
#     # else:
#     #     # might have a link as a retweet?
#     #     url = tweet_payload['object']['link']
#     #     text += u"\n{}".format(url)
#
#     # grab links any text associated with them
#     for link in tweet.links.all():
#         if "twitter.com" not in link.expanded_url:
#             try:
#                 text += u"\n{}\n{}\n{}".format(link.expanded_url,
#                                                link.tw_expanded_url_title,
#                                                link.tw_expanded_url_description)
#             except:
#                 try: text += u"\n{}\n{}\n{}".format(decode_text(link.expanded_url),
#                                                     decode_text(link.tw_expanded_url_title),
#                                                     decode_text(link.tw_expanded_url_description))
#                 except:
#                     # we tried, it's just not happening
#                     pass
#
#
#     return text


def load_tweet(tweet_payload, rt_match, options, kwquery=None):

    # There's always an information summary tweet, which we want to skip
    try:
        if tweet_payload.get("id"):
            # check if the tweet exists. If it does, we don't need to do anything
            try:
                existing = Tweet.objects.get(tw_id=tweet_payload["id"].split(":")[-1])
                if not existing.gnip:
                    icantbelieveimdoingthis_prefix, icantbelieveimdoingthis_suffix = (
                        existing.tw_id[:-1],
                        existing.tw_id[-1:],
                    )
                    mapper_of_shame = {
                        "0": "a",
                        "1": "b",
                        "2": "c",
                        "3": "d",
                        "4": "e",
                        "5": "f",
                        "6": "g",
                        "7": "h",
                        "8": "i",
                        "9": "j",
                        "mysoul": "emptyinside",
                    }
                    thisistheworstthingiveeverdone = mapper_of_shame[
                        icantbelieveimdoingthis_suffix
                    ]
                    existing.tw_id = (
                        icantbelieveimdoingthis_prefix + thisistheworstthingiveeverdone
                    )
                    existing.save()
                    existing = None
            except:
                existing = None
            # if not Tweet.objects.filter(gnip=True).filter(tw_id=tweet_payload['id'].split(':')[-1]).exists():
            if not existing:
                # try:
                tweet = Tweet()
                tweet.tw_id = tweet_payload["id"].split(":")[-1]
                tweet.json = tweet_payload
                tweet.gnip = True
                # tweet.text = get_body_text(tweet_payload, rt_match)
                tweet.batch_id = (
                    3
                )  # TODO: good lord this should be using the batch_id that for some reason is a keyword parameter
                tweet.save()
                tweet.extract_text()
                tweet.extract_links(
                    extract_secondary_links=options["extract_secondary_links"],
                    save=True,
                    process=True,
                )

                if kwquery:
                    # first is immigration
                    tweet.keyword_queries.add(kwquery)
                    tweet.save()
                # except IntegrityError, e:
                #    print("Could not do initial save of tweet {}.\n Message: {}".format(tweet_payload['id']), e)

    except Exception as e:
        print(e)
