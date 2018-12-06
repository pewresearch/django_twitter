from django.conf import settings
from django.core.management.base import BaseCommand
from django.apps import apps

from pewtils.django import get_model

from tqdm import tqdm

from pewhooks.twitter import TwitterAPIHandler


class Command(BaseCommand):

    def add_arguments(self, parser):

        parser.add_argument("twitter_id", type = str)
        parser.add_argument("--ignore_backfill", action="store_true", default=False)
        parser.add_argument("--overwrite", action="store_true", default=False)
        parser.add_argument("--tweet_set", type = str)
        parser.add_argument("--no_progress_bar", action="store_true", default=False)

        parser.add_argument('--api_key', type=str)
        parser.add_argument('--api_secret', type=str)
        parser.add_argument('--access_token', type=str)
        parser.add_argument('--access_secret', type=str)

    def handle(self, *args, **options):

        self.twitter = TwitterAPIHandler(
            api_key=options["api_key"],
            api_secret=options["api_secret"],
            access_token=options["access_token"],
            access_secret=options["access_secret"]
        )

        tweet_set = None
        if options["tweet_set"]:
            tweet_set_model = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWEET_SET_MODEL)
            tweet_set, created = tweet_set_model.objects.get_or_create(name=options["tweet_set"])

        scanned_count, updated_count = 0, 0
        user_model = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWITTER_PROFILE_MODEL)
        twitter_json = self.twitter.get_user(options["twitter_id"])
        if twitter_json:
            twitter_user, created = user_model.objects.get_or_create(twitter_id=twitter_json.id_str)

            tweet_model = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWEET_MODEL)
            # Get list of current tweets
            existing_tweets = list(twitter_user.tweets.values_list('twitter_id', flat=True))

            # Iterate through all tweets in timeline

            if options['no_progress_bar']:
                iterator = self.twitter.iterate_user_timeline(options['twitter_id'])
            else:
                iterator = tqdm(self.twitter.iterate_user_timeline(options['twitter_id']),
                                desc = "Retrieving tweets for user {}".format(twitter_user.screen_name))
            print("Retrieving tweets for user {}".format(twitter_user.screen_name))
            for tweet_json in iterator:
                keep_pulling, updated_count, scanned_count = \
                    self.save_tweet(tweet_model, tweet_json, tweet_set, existing_tweets,
                                    options['overwrite'], options['ignore_backfill'],
                                    twitter_user.tweet_backfilled, updated_count, scanned_count)

                if not keep_pulling:
                    break

                # if (options['overwrite'] or options['ignore_backfill']) or \
                #     (tweet_json.id_str not in existing_tweets):
                #
                #     tweet, created = tweet_model.objects.get_or_create(
                #         twitter_id=tweet_json.id_str
                #     )
                #     tweet.update_from_json(tweet_json._json)
                #     if tweet_set:
                #         tweet_set.tweets.add(tweet)
                #     updated_count += 1
                #     scanned_count += 1
                # elif twitter_user.tweet_backfilled and \
                #         ((not options['ignore_backfill']) or \
                #         (tweet_json.id_str in existing_tweets)):
                #     print("Encountered existing tweet, stopping now")
                #     break
                # else:
                #     print("Reached end of tweets, stopping")
                #     break

            twitter_user.tweet_backfilled = True
            twitter_user.save()
            print("{}: {} tweets scanned, {} updated".format(str(twitter_user), scanned_count, updated_count))

    def save_tweet(self, tweet_model, tweet_json, tweet_set, existing_tweets, overwrite, ignore_backfill, backfilled,
                        updated_count, scanned_count):

        if overwrite or (tweet_json.id_str not in existing_tweets):
            # Only write a tweet if you're overwriting, or it doesn't already exist
            tweet, created = tweet_model.objects.get_or_create(
                twitter_id=tweet_json.id_str
            )
            tweet.update_from_json(tweet_json._json)
            tweet.update_relations_from_json(tweet_json._json)
            if tweet_set:
                tweet_set.tweets.add(tweet)
            updated_count += 1
            scanned_count += 1

        if backfilled and tweet_json.id_str in existing_tweets and not ignore_backfill:
            # Only stop if the account has been backfilled and you encounter an existing tweet
            print("Encountered existing tweet, stopping now")
            return (False, updated_count, scanned_count)
        else:
            return (True, updated_count, scanned_count)
