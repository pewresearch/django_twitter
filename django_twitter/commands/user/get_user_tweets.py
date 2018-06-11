from django.conf import settings

from django_commender.commands import BasicCommand, commands, log_command
from pewtils.django import get_model

from tqdm import tqdm

from pewhooks import TwitterAPIHandler

class Command(BasicCommand):

    parameter_names = ["twitter_id", "ignore_backfill", "overwrite"]
    dependencies = []

    @staticmethod
    def add_arguments(parser):
        parser.add_argument("-id", "twitter_id", type=str)
        parser.add_argument("ignore_backfill", default=False, type=bool)
        parser.add_argument("overwrite", default=False, type=bool)

    def __init__(self, **options):
        super(Command, self).__init__(**options)
        self.twitter = TwitterAPIHandler()

    @log_command
    def run(self):

        scanned_count, updated_count = 0, 0
        twitter_user = get_model(settings.getattr('TWITTER_USER_MODEL')).objects.create_or_update(
            {'twitter_id': self.parameters['twitter_id']},
            return_object=True
        )

        # get list of current tweets
        existing_tweets = list(twitter_user.tweets.values_list('twitter_id', flat=True))
        # Next line was in the original - I don't think we need it here but leaving it in (commented) in case things break
        #existing_tweets.extend(flatten_list(list(profile.tweets.values_list("duplicate_twitter_ids", flat=True))))


        # Iterate through all tweets in timeline
        for tweet_json in tqdm(self.twitter.iterate_user_followers(self.parameters['twitter_id']),
                                desc = "Retrieving tweets for user {}".format(twitter_user.screen_name)):
            if not twitter_user.tweet_backfilled or \
                    self.parameters["ignore_backfill"] or self.parameters["overwrite"] or \
                    tweet_json['id_str'] not in existing_tweets:

                if self.parameters['overwrite'] or tweet['id_str'] not in existing_tweets:
                    tweet = get_model(settings.getattr('TWITTER_TWEET_MODEL')).objects.create_or_update(
                        {'twitter_id': self.parameters['twitter_id']},
                        return_object=True
                    )
                    tweet.update_from_json(tweet_json)
                    updated_count += 1
                elif twitter_user.tweet_backfill and not self.parameters['ignore_backfill']:
                    print("Encountered existing tweet, stopping now")
                    break
                scanned_count += 1
            else:
                print("Reached end of tweets, stopping")
                break

        twitter_user.tweet_backfilled = True
        print "{}: {} tweets scanned, {} updated".format(str(twitter_user), scanned_count, updated_count)



