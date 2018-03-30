import tweepy, datetime, time, re, botometer, os, pandas

from pandas.io.json import json_normalize
from tqdm import tqdm
from django.conf import settings

from logos.models import Politician, TwitterProfile, Tweet, Year, TwitterHashtag
from django_learning.models import Document
from pewtils import is_not_null
from pewtils.twitter import TwitterAPIHandler

from django_commander.commands import IterateDownloadCommand


class Command(IterateDownloadCommand):
    """
        Iterates over Politician objects with non-null twitter_id fields, and pulls the latest tweets from their
        timeline. Once a politician's full timeline has been processed (from what's avaialble), the backfill flag gets
        set. For politicians with a known backfill, the iterator will break early once it encounters an existing tweet.
        This ensures that if the syncing process is interrupted before it finishes for a given politician, it will
        iterate completely the next time the command is run.
    """

    @staticmethod
    def add_arguments(parser):
        parser.add_argument("--ignore_backfill", action="store_true", default=False)
        parser.add_argument("--overwrite", action="store_true", default=False)
        parser.add_argument("--bioguide_id", default=None, type=str)
        parser.add_argument("--profile_id", default=None, type=int)
        return parser

    parameter_names = []
    dependencies = [
        ("load_united_states_github_congress_members", {}),
        ("load_united_states_github_congress_member_social_media", {}),
        ("load_twitter_politician_profiles", {})
    ]

    def __init__(self, **options):

        self.api = TwitterAPIHandler()

        self.counts = 0
        self.errors = 0

        self.twitter_app_auth = {
            'consumer_key': os.environ.get("TWITTER_API_KEY", None),
            'consumer_secret': os.environ.get("TWITTER_API_SECRET", None),
            'access_token': os.environ.get("TWITTER_API_ACCESS_TOKEN", None),
            'access_token_secret': os.environ.get("TWITTER_API_ACCESS_SECRET", None)
        }
        self.botometer = self.get_botometer_connection()

        super(Command, self).__init__(**options)

    def iterate(self):

        # TODO: get rid of the botometer scores filter after this after first sync
        profiles = TwitterProfile.objects \
            .filter(politician__isnull=False) \
            .filter(botometer_scores_english__isnull=True) \
            .filter(historical=False) \
            .order_by("?")
        if self.options["bioguide_id"]:
            profiles = profiles.filter(politician__bioguide_id=self.options["bioguide_id"])
        if self.options["profile_id"]:
            profiles = profiles.filter(pk=self.options["profile_id"])
        for profile in tqdm(profiles.distinct(), "Loading politician Twitter Botometer scores", leave=True):
            yield [profile, ]
            if self.options["test"]: break

    def download(self, profile):

        ids = [profile.twitter_id]
        try:
            results = [r for r in self.botometer.check_accounts_in(ids)]
        except Exception as e:
            try:
                print "Botometer error, trying reconnect: {}".format(e)
                self.botometer = self.get_botometer_connection()
                results = [r for r in self.botometer.check_accounts_in(ids)]
            except Exception as e:
                print "Error, and reconnect didn't work!  Botometer is angry: {}".format(e)
                import pdb
                pdb.set_trace()
        if results:
            results = self.flatten_results(results)
            self.save_results(results)
        print "Checked {} ({} successful, {} errors)".format(profile, self.counts, self.errors)

        return [None, ]

    def get_botometer_connection(self):

        return botometer.Botometer(
            mashape_key=settings.MASHAPE_KEY,
            **self.twitter_app_auth
        )

    def flatten_results(self, results):

        columns = [u'categories.content', u'categories.friend', u'categories.network',
                   u'categories.sentiment', u'categories.temporal', u'categories.user',
                   u'scores.english', u'scores.universal', u'user.id_str',
                   u'user.screen_name']
        df = pandas.DataFrame(columns=columns)
        for user in results:
            row = json_normalize(user[1])
            df = df.append(row)
        return df

    def save_results(self, df):

        for ind, row in df.iterrows():

            try:

                t = TwitterProfile.objects.get_if_exists({"twitter_id": row['user.id_str']})
                if t:
                    t.botometer_content = row['categories.content']
                    t.botometer_temporal = row['categories.temporal']
                    t.botometer_friend = row['categories.friend']
                    t.botometer_network = row['categories.network']
                    t.botometer_user = row['categories.user']
                    t.botometer_scores_english = row['scores.english']
                    t.botometer_scores_universal = row['scores.universal']
                    t.botometer_sentiment = row['categories.sentiment']
                    t.save()
                    self.counts += 1
                    print "{}: {}".format(t, t.botometer_scores_english)
                else:
                    self.errors += 1

            except Exception as rowError:

                print "Botometer error: {}".format(rowError)
                self.errors += 1

        return [None, ]

    def cleanup(self):

        pass