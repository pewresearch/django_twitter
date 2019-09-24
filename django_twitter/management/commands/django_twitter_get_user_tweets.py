from __future__ import print_function
from builtins import str
from django.conf import settings
from django.core.management.base import BaseCommand
from django.apps import apps

from tqdm import tqdm
from dateutil.parser import parse as date_parse

from pewhooks.twitter import TwitterAPIHandler

from django_twitter.utils import get_twitter_user


class Command(BaseCommand):
    def add_arguments(self, parser):

        parser.add_argument("twitter_id", type=str)
        parser.add_argument("--ignore_backfill", action="store_true", default=False)
        parser.add_argument("--overwrite", action="store_true", default=False)
        parser.add_argument("--max_backfill_date", type=str)
        parser.add_argument("--tweet_set_name", type=str)
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
        if options["tweet_set_name"]:
            tweet_set_model = apps.get_model(
                app_label=settings.TWITTER_APP, model_name=settings.TWEET_SET_MODEL
            )
            tweet_set, created = tweet_set_model.objects.get_or_create(
                name=options["tweet_set_name"]
            )

        scanned_count, updated_count = 0, 0
        user_model = apps.get_model(
            app_label=settings.TWITTER_APP, model_name=settings.TWITTER_PROFILE_MODEL
        )
        twitter_json = get_twitter_user(options["twitter_id"], self.twitter)
        if twitter_json:
            try:
                twitter_user, created = user_model.objects.get_or_create(
                    twitter_id=twitter_json.id_str
                )
            except user_model.MultipleObjectsReturned:
                print(
                    "Warning: multiple users found for {}".format(twitter_json.id_str)
                )
                print(
                    "For flexibility, Django Twitter does not enforce a unique constraint on twitter_id"
                )
                print(
                    "But in this case it can't tell which user to use, so it's picking the most recently updated one"
                )
                twitter_user = user_model.objects.filter(
                    twitter_id=twitter_json.id_str
                ).order_by("-last_update_time")[0]

            tweet_model = apps.get_model(
                app_label=settings.TWITTER_APP, model_name=settings.TWEET_MODEL
            )
            # Get list of current tweets
            existing_tweets = list(
                twitter_user.tweets.values_list("twitter_id", flat=True)
            )

            # Iterate through all tweets in timeline

            if options["no_progress_bar"]:
                iterator = self.twitter.iterate_user_timeline(
                    options["twitter_id"], return_errors=True
                )
            else:
                iterator = tqdm(
                    self.twitter.iterate_user_timeline(
                        options["twitter_id"], return_errors=True
                    ),
                    desc="Retrieving tweets for user {}".format(
                        twitter_user.screen_name
                    ),
                )

            print("Retrieving tweets for user {}".format(twitter_user.screen_name))
            keep_pulling = True
            for tweet_json in iterator:
                if type(tweet_json) == int:
                    twitter_user.is_private = True
                    twitter_user.save()
                    print("User {} is private".format(twitter_user.screen_name))
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

                    keep_pulling = True
                    if (
                        twitter_user.tweet_backfilled
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

            twitter_user.tweet_backfilled = True
            twitter_user.save()
            print(
                "{}: {} tweets scanned, {} updated".format(
                    str(twitter_user), scanned_count, updated_count
                )
            )
