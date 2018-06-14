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
        try: twitter_user = user_model.objects.get(twitter_id=options["twitter_id"])
        except user_model.DoesNotExist: twitter_user = user_model.objects.create(twitter_id=options["twitter_id"])

        # get list of current tweets
        existing_tweets = list(twitter_user.tweets.values_list('twitter_id', flat=True))
        # Next line was in the original - I don't think we need it here but leaving it in (commented) in case things break
        #existing_tweets.extend(flatten_list(list(profile.tweets.values_list("duplicate_twitter_ids", flat=True))))


        # Iterate through all tweets in timeline
        import pdb
        pdb.set_trace()
        for tweet_json in tqdm(self.twitter.iterate_user_timeline(options['twitter_id']),
                                desc = "Retrieving tweets for user {}".format(twitter_user.screen_name)):
            if not twitter_user.tweet_backfilled or \
                    options["ignore_backfill"] or options["overwrite"] or \
                    tweet_json.id_str not in existing_tweets:

                if options['overwrite'] or tweet_json.id_str not in existing_tweets:
                    tweet = apps.get_model(app_label="test_app", model_name=settings.TWITTER_PROFILE_MODEL).objects.get_or_create(
                        {'twitter_id': options['twitter_id']}
                    )
                    tweet.update_from_json(tweet_json)
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



