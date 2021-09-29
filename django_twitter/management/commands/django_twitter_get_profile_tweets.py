from __future__ import print_function

import datetime

from builtins import str
from django.conf import settings
from django.core.management.base import BaseCommand
from django.apps import apps

from tqdm import tqdm
from dateutil.parser import parse as date_parse

from pewhooks.twitter import TwitterAPIHandler
from django_pewtils import reset_django_connection

from django_twitter.utils import (
    get_twitter_profile_json,
    safe_get_or_create,
    get_concrete_model,
)


class Command(BaseCommand):
    """
    Download and save the tweets for a specific profile. The first time this command is run, it will loop over \
    the profile's tweets in reverse-chronological order as far back as it can go (~3200 tweets). In subsequent \
    calls to this command, it will break off when it encounters an existing tweet. Passing `--ignore_backfill` \
    will override this behavior. Additionally passing `--max_backfill_date` or `--max_backfill_days` will override \
    this behavior but only for recent tweets. By default, Django Twitter does not update data for existing tweets \
    by default; to override this behavior you can pass `--overwrite`.

    :param profile_set: The `name` of the profile set in the database
    :param add_to_profile_set: (Optional) The name of a profile set to add the profile to. Can be \
    any arbitrary string you want to use; if the profile set doesn't already exist, it will be created
    :param add_to_tweet_set: (Optional) The name of a tweet set to add each tweet to. Can be \
    any arbitrary string you want to use; if the tweet set doesn't already exist, it will be created.
    :param ignore_backfill: (Optional) By default, Django Twitter will only iterate through a profile's full tweet \
    timeline the first time it runs. Once it has successfully iterated through all of a profile's tweets once before, \
    subsequent calls to this command will break off when they encounter an existing tweet. Passing \
    `--ignore_backfill` to this command will override this behavior and force it to iterate the whole timeline.
    :param overwrite: (Optional) By default, Django Twitter will skip over any existing tweets and will not \
    overwrite any of their data. If you pass `--overwrite` this behavior will be overridden, and if the command \
    encounters existing tweets (e.g. if you have also passed `--ignore_backfill`) then it will update them with \
    the latest API data.
    :param max_backfill_date: (Optional) A YYYY-MM-DD or MM-DD-YYYY string representing a date at which the \
    `ignore_backfill` behavior should stop. Useful if you want to iterate over and refresh previously-collected \
    tweets (i.e. by also passing `--ignore_backfill` and `--overwrite`) and refresh their stats, but only for \
    recent tweets that were created after a certain date.
    :param max_backfill_days: (Optional) Alternative to `max_backfill_date`; overrides the `--ignore_backfill` \
    behavior but only for tweets that were created within the last N days.
    :param no_progress_bar: (Optional) Disables the default `tqdm` progress bar.
    :param limit: (Optional) Set a limit for the number of tweets to collect for each profile, for testing purposes.

    :param api_key: (Optional) Twitter API key, if you don't have the TWITTER_API_KEY environment variable set
    :param api_secret: (Optional) Twitter API secret, if you don't have the TWITTER_API_SECRET environment variable set
    :param access_token: (Optional) Twitter access token, if you don't have the TWITTER_API_ACCESS_TOKEN environment \
    variable set
    :param api_secret: (Optional) Twitter API access secret, if you don't have the TWITTER_API_ACCESS_SECRET \
    environment variable set
    """

    def add_arguments(self, parser):

        parser.add_argument("twitter_id", type=str)
        parser.add_argument("--add_to_profile_set", type=str)
        parser.add_argument("--add_to_tweet_set", type=str)
        parser.add_argument("--ignore_backfill", action="store_true", default=False)
        parser.add_argument("--overwrite", action="store_true", default=False)
        group = parser.add_mutually_exclusive_group(required=False)
        group.add_argument("--max_backfill_date", type=str)
        group.add_argument("--max_backfill_days", type=int)
        parser.add_argument("--no_progress_bar", action="store_true", default=False)
        parser.add_argument("--limit", type=int, default=None)

        parser.add_argument("--api_key", type=str)
        parser.add_argument("--api_secret", type=str)
        parser.add_argument("--access_token", type=str)
        parser.add_argument("--access_secret", type=str)

    def handle(self, *args, **options):

        reset_django_connection()

        self.twitter = TwitterAPIHandler(
            api_key=options["api_key"],
            api_secret=options["api_secret"],
            access_token=options["access_token"],
            access_secret=options["access_secret"],
        )

        max_backfill_date = None
        if options["max_backfill_date"]:
            max_backfill_date = date_parse(options["max_backfill_date"])
        elif options["max_backfill_days"]:
            max_backfill_date = datetime.datetime.now() - datetime.timedelta(
                days=options["max_backfill_days"]
            )
            max_backfill_date = datetime.datetime(
                max_backfill_date.year, max_backfill_date.month, max_backfill_date.day
            )
        tweet_set = None
        if options["add_to_tweet_set"]:
            tweet_set = safe_get_or_create(
                "AbstractTweetSet", "name", options["add_to_tweet_set"], create=True
            )

        twitter_profile_set = None
        if options["add_to_profile_set"]:
            twitter_profile_set = safe_get_or_create(
                "AbstractTwitterProfileSet",
                "name",
                options["add_to_profile_set"],
                create=True,
            )

        scanned_count, updated_count = 0, 0
        twitter_json = get_twitter_profile_json(options["twitter_id"], self.twitter)
        if twitter_json:
            twitter_profile = safe_get_or_create(
                "AbstractTwitterProfile", "twitter_id", twitter_json.id_str
            )
            snapshot = get_concrete_model(
                "AbstractTwitterProfileSnapshot"
            ).objects.create(profile=twitter_profile)
            snapshot.update_from_json(twitter_json._json)
            twitter_profile.twitter_error_code = None
            twitter_profile.save()

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
                    print("User {} is private".format(twitter_profile.screen_name))
                    break
                else:

                    scanned_count += 1
                    existing_related = 0
                    if options["overwrite"] or (
                        tweet_json.id_str not in existing_tweets
                    ):
                        # Only write a tweet if you're overwriting, or it doesn't already exist
                        tweet = safe_get_or_create(
                            "AbstractTweet",
                            "twitter_id",
                            tweet_json.id_str,
                            create=True,
                        )
                        tweet.update_from_json(tweet_json._json)
                        if tweet_set:
                            tweet_set.tweets.add(tweet)
                        updated_count += 1
                        # Check to see if there are already existing relations that were created by another tweet
                        existing_related += (
                            tweet.replies.count()
                            + tweet.retweets.count()
                            + tweet.replies.count()
                        )
                        if not tweet.text:
                            import pdb

                            pdb.set_trace()
                    if (
                        twitter_profile.tweet_backfilled
                        and tweet_json.id_str in existing_tweets
                        and not options["ignore_backfill"]
                    ):
                        if existing_related == 0:
                            # Only stop if the account has been backfilled and you encounter an existing tweet
                            # With one exception: if another profile replied to, retweeted, or quoted this tweet
                            # Then it may have already existed in the database even though we didn't necessarily
                            # collect it when we were iterating over this user's timeline.
                            # So if references to this tweet already exist in the database, it's not useful for
                            # determining whether we've previously backfilled this profile
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
