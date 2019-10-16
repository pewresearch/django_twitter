from __future__ import print_function
from builtins import str
from django.conf import settings
from django.core.management.base import BaseCommand
from django.apps import apps

from tqdm import tqdm
from dateutil.parser import parse as date_parse

from pewhooks.twitter import TwitterAPIHandler

from django_twitter.utils import (
    get_twitter_profile_json,
    get_twitter_profile,
    get_tweet_set,
    get_twitter_profile_set,
)


class Command(BaseCommand):
    def add_arguments(self, parser):

        parser.add_argument("twitter_id", type=str)
        parser.add_argument("--add_to_profile_set", type=str)
        parser.add_argument("--add_to_tweet_set", type=str)
        parser.add_argument("--ignore_backfill", action="store_true", default=False)
        parser.add_argument("--overwrite", action="store_true", default=False)
        parser.add_argument("--max_backfill_date", type=str)
        parser.add_argument("--no_progress_bar", action="store_true", default=False)
        parser.add_argument("--limit", type=int, default=None)

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

        max_backfill_date = None
        if options["max_backfill_date"]:
            max_backfill_date = date_parse(options["max_backfill_date"])

        tweet_set = None
        if options["add_to_tweet_set"]:
            tweet_set = get_tweet_set(options["add_to_tweet_set"])

        twitter_profile_set = None
        if options["add_to_profile_set"]:
            twitter_profile_set = get_twitter_profile_set(options["add_to_profile_set"])

        scanned_count, updated_count = 0, 0
        twitter_json = get_twitter_profile_json(options["twitter_id"], self.twitter)
        if twitter_json:
            twitter_profile = get_twitter_profile(twitter_json.id_str)

            tweet_model = apps.get_model(
                app_label=settings.TWITTER_APP, model_name=settings.TWEET_MODEL
            )
            # Get list of current tweets
            existing_tweets = list(
                twitter_profile.tweets.values_list("twitter_id", flat=True)
            )

            # Iterate through all tweets in timeline

            if options["no_progress_bar"]:
                iterator = self.twitter.iterate_profile_timeline(
                    options["twitter_id"], return_errors=True
                )
            else:
                iterator = tqdm(
                    self.twitter.iterate_profile_timeline(
                        options["twitter_id"], return_errors=True
                    ),
                    desc="Retrieving tweets for user {}".format(
                        twitter_profile.screen_name
                    ),
                )

            print("Retrieving tweets for user {}".format(twitter_profile.screen_name))
            keep_pulling = True
            for tweet_json in iterator:
                if type(tweet_json) == int:
                    twitter_profile.is_private = True
                    twitter_profile.save()
                    print("User {} is private".format(twitter_profile.screen_name))
                    break
                else:

                    scanned_count += 1
                    if options["overwrite"] or (
                        tweet_json.id_str not in existing_tweets
                    ):
                        # Only write a tweet if you're overwriting, or it doesn't already exist
                        tweet, created = tweet_model.objects.get_or_create(
                            twitter_id=tweet_json.id_str
                        )
                        tweet.update_from_json(tweet_json._json)
                        if tweet_set:
                            tweet_set.tweets.add(tweet)
                        updated_count += 1
                        if not tweet.text:
                            import pdb

                            pdb.set_trace()
                    if (
                        twitter_profile.tweet_backfilled
                        and tweet_json.id_str in existing_tweets
                        and not options["ignore_backfill"]
                    ):
                        # Only stop if the account has been backfilled and you encounter an existing tweet
                        print("Encountered existing tweet, stopping now")
                        keep_pulling = False
                    elif max_backfill_date:
                        timestamp = date_parse(
                            tweet_json._json["created_at"], ignoretz=True
                        )
                        if timestamp < max_backfill_date:
                            print("Reached the limit of ignore_backfill")
                            keep_pulling = False
                    if options["limit"] and scanned_count >= options["limit"]:
                        keep_pulling = False

                if not keep_pulling:
                    break

            twitter_profile.tweet_backfilled = True
            twitter_profile.save()
            if twitter_profile_set:
                twitter_profile_set.profiles.add(twitter_profile)
            print(
                "{}: {} tweets scanned, {} updated".format(
                    str(twitter_profile), scanned_count, updated_count
                )
            )
