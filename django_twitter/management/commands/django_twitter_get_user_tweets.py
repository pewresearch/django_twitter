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

    def __init__(self, **options):

        super(Command, self).__init__(**options)
        self.twitter = TwitterAPIHandler()

    def handle(self, *args, **options):

        scanned_count, updated_count = 0, 0
        user_model = apps.get_model(app_label="test_app", model_name=settings.TWITTER_PROFILE_MODEL)
        twitter_user, created = user_model.objects.get_or_create(twitter_id=options["twitter_id"])

        tweet_model = apps.get_model(app_label="test_app", model_name=settings.TWEET_MODEL)
        # Get list of current tweets
        existing_tweets = list(twitter_user.tweets.values_list('twitter_id', flat=True))
        # Iterate through all tweets in timeline
        for tweet_json in tqdm(self.twitter.iterate_user_timeline(options['twitter_id']),
                                desc = "Retrieving tweets for user {}".format(twitter_user.screen_name)):
            if not twitter_user.tweet_backfilled or \
                    options["ignore_backfill"] or options["overwrite"] or \
                    tweet_json.id_str not in existing_tweets:

                if options['overwrite'] or tweet_json.id_str not in existing_tweets:
                    tweet, created = tweet_model.objects.get_or_create(
                        twitter_id=options['twitter_id']
                    )
                    tweet.update_from_json(tweet_json._json)
                    updated_count += 1
                elif twitter_user.tweet_backfill and not options['ignore_backfill']:
                    print("Encountered existing tweet, stopping now")
                    break
                scanned_count += 1
            else:
                print("Reached end of tweets, stopping")
                break

        twitter_user.tweet_backfilled = True
        print "{}: {} tweets scanned, {} updated".format(str(twitter_user), scanned_count, updated_count)



