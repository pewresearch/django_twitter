from __future__ import unicode_literals
from builtins import str

import unittest
import copy
import datetime
import json

from django.test import TestCase as DjangoTestCase
from django.core.management import call_command
from django.conf import settings
from django.apps import apps

# TODO: if you try to override the settings, it fails because the models.py files get loaded before the settings
#  get overwritten, so the conditionals in models.py use the testapp.settings.py defaults instead of the overrides.
#  There may be a way to modify django_twitter.apps to conditionally load or ignore the models rather than hard-code
#  a conditional into models.py, but I haven't figured that out yet
# migrations = copy.deepcopy(settings.MIGRATION_MODULES)
# migrations["testapp"] = "testapp.migrations.django_twitter_models"
# @override_settings(TWITTER_APP="django_twitter", MIGRATION_MODULES=migrations)
class DjangoTwitterTests(DjangoTestCase):

    """
    To test, navigate to django_twitter root folder and run `python manage.py test testapp.tests`
    """

    def setUp(self):

        from django_twitter.utils import get_concrete_model

        self.TwitterProfile = get_concrete_model("AbstractTwitterProfile")
        self.TwitterProfileSnapshot = get_concrete_model(
            "AbstractTwitterProfileSnapshot"
        )
        self.TwitterProfileSet = get_concrete_model("AbstractTwitterProfileSet")
        self.Tweet = get_concrete_model("AbstractTweet")
        self.TweetSet = get_concrete_model("AbstractTweetSet")
        self.TwitterFollowerList = get_concrete_model("AbstractTwitterFollowerList")
        self.TwitterFollowingList = get_concrete_model("AbstractTwitterFollowingList")
        self.TwitterHashtag = get_concrete_model("AbstractTwitterHashtag")

    def test_user_commands(self):

        call_command(
            "django_twitter_get_profile", "pvankessel", add_to_profile_set="get_profile"
        )
        self.assertEqual(
            self.TwitterProfile.objects.filter(screen_name="pvankessel").count(), 1
        )
        profile = self.TwitterProfile.objects.get(screen_name="pvankessel")
        self.assertIsNotNone(profile.twitter_id)
        self.assertIsNotNone(profile.created_at)
        self.assertIsNotNone(profile.screen_name)
        self.assertGreater(profile.snapshots.count(), 0)
        for snapshot in profile.snapshots.all():
            snapshot.json = json.dumps(snapshot.json)
            snapshot.save()
            snapshot.update_from_json()
            self.assertIsNotNone(snapshot.followers_count)
            self.assertIsNotNone(snapshot.description)
            self.assertIsNotNone(snapshot.favorites_count)
        self.assertIsNotNone(profile.most_recent_snapshot)
        profile.most_recent_snapshot.delete()
        profile.refresh_from_db()
        self.assertIsNotNone(profile.pk)

        call_command(
            "django_twitter_get_profile_set",
            "get_profile",
            num_cores=1,
            add_to_profile_set="get_profile_set",
        )
        self.assertEqual(
            profile.twitter_profile_sets.filter(name="get_profile_set").count(), 1
        )

        call_command(
            "django_twitter_get_profile_followers",
            profile.twitter_id,
            add_to_profile_set="get_profile_followers",
            limit=5,
        )
        self.assertGreater(profile.follower_lists.count(), 0)
        self.assertGreater(profile.current_followers().count(), 0)
        call_command(
            "django_twitter_get_profile_set_followers",
            "get_profile",
            num_cores=1,
            add_to_profile_set="get_profile_set_followers",
            limit=5,
        )
        self.assertGreater(
            self.TwitterProfileSet.objects.get(
                name="get_profile_set_followers"
            ).profiles.count(),
            1,
        )

        call_command(
            "django_twitter_get_profile_followings",
            profile.twitter_id,
            add_to_profile_set="get_profile_followings",
            limit=5,
        )
        self.assertGreater(profile.following_lists.count(), 0)
        self.assertGreater(profile.current_followings().count(), 0)
        call_command(
            "django_twitter_get_profile_set_followings",
            "get_profile",
            num_cores=1,
            add_to_profile_set="get_profile_set_followings",
            limit=5,
        )
        self.assertGreater(
            self.TwitterProfileSet.objects.get(
                name="get_profile_set_followings"
            ).profiles.count(),
            1,
        )

        call_command(
            "django_twitter_get_profile_tweets",
            profile.twitter_id,
            limit=50,
            add_to_profile_set="get_profile_tweets",
            add_to_tweet_set="get_profile_tweets",
        )
        correct_num_tweets = profile.tweets.count()
        self.assertGreater(correct_num_tweets, 0)
        for tweet in self.TweetSet.objects.get(name="get_profile_tweets").tweets.all()[
            :5
        ]:
            self.assertIsNotNone(tweet.twitter_id)
            self.assertIsNotNone(tweet.text)
            self.assertIsNotNone(tweet.created_at)
            self.assertIsNotNone(tweet.retweet_count)
            self.assertIsNotNone(tweet.favorite_count)
            self.assertEqual(tweet.profile, profile)
        tweet.json = json.dumps(tweet.json)
        tweet.save()
        tweet.update_from_json()

        # Test with max_backfill_date
        limit1 = profile.tweets.order_by("created_at")[25].created_at
        limit2 = profile.tweets.order_by("created_at")[45].created_at
        profile.tweets.filter(created_at__lt=limit2).delete()
        num_tweets = profile.tweets.count()
        self.assertLess(num_tweets, correct_num_tweets)
        call_command(
            "django_twitter_get_profile_tweets",
            profile.twitter_id,
            ignore_backfill=True,
            max_backfill_date=limit1.strftime("%Y-%m-%d"),
            limit=50,
            add_to_profile_set="get_profile_tweets",
            add_to_tweet_set="get_profile_tweets",
        )
        self.assertGreater(profile.tweets.count(), num_tweets)
        num_tweets = profile.tweets.count()
        self.assertLess(num_tweets, correct_num_tweets)
        call_command(
            "django_twitter_get_profile_tweets",
            profile.twitter_id,
            ignore_backfill=True,
            limit=50,
            add_to_profile_set="get_profile_tweets",
            add_to_tweet_set="get_profile_tweets",
        )
        self.assertGreaterEqual(profile.tweets.count(), correct_num_tweets)

        # Test with max_backfill_days
        limit1 = profile.tweets.order_by("created_at")[25].created_at
        limit2 = profile.tweets.order_by("created_at")[45].created_at
        profile.tweets.filter(created_at__lt=limit2).delete()
        num_tweets = profile.tweets.count()
        self.assertLess(num_tweets, correct_num_tweets)
        call_command(
            "django_twitter_get_profile_tweets",
            profile.twitter_id,
            ignore_backfill=True,
            max_backfill_days=(datetime.datetime.now() - limit1).days,
            limit=50,
            add_to_profile_set="get_profile_tweets",
            add_to_tweet_set="get_profile_tweets",
        )
        self.assertGreater(profile.tweets.count(), num_tweets)
        num_tweets = profile.tweets.count()
        self.assertLess(num_tweets, correct_num_tweets)
        call_command(
            "django_twitter_get_profile_tweets",
            profile.twitter_id,
            ignore_backfill=True,
            limit=50,
            add_to_profile_set="get_profile_tweets",
            add_to_tweet_set="get_profile_tweets",
        )
        self.assertGreaterEqual(profile.tweets.count(), correct_num_tweets)

        call_command(
            "django_twitter_get_profile_set_tweets",
            "get_profile_tweets",
            num_cores=1,
            ignore_backfill=True,
            limit=50,
            add_to_profile_set="get_profile_set_tweets",
            add_to_tweet_set="get_profile_set_tweets",
            overwrite=True,  # this is so we don't skip over adding tweets to the tweet set
        )
        self.assertEqual(
            profile.twitter_profile_sets.filter(name="get_profile_set_tweets").count(),
            1,
        )
        self.assertGreater(
            self.TweetSet.objects.get(name="get_profile_set_tweets").tweets.count(), 0
        )

        self.assertGreater(self.TwitterProfile.objects.count(), 0)
        self.assertGreater(self.TwitterFollowerList.objects.count(), 0)
        self.assertGreater(self.TwitterFollowingList.objects.count(), 0)
        self.assertGreater(self.TwitterHashtag.objects.count(), 0)

    def test_utility_functions(self):

        from django_twitter.utils import (
            identify_unusual_profiles_by_descriptions,
            identify_unusual_profiles_by_tweet_text,
            get_monthly_twitter_activity,
            find_missing_date_ranges,
            get_twitter_profile_dataframe,
            get_tweet_dataframe,
        )

        # We're going to assume that Justin Bieber will always be quite distinctive from the Pew accounts
        # And that none of these accounts will disappear anytime soon
        for handle in [
            "pewresearch",
            "pewglobal",
            "pewmethods",
            "pewjournalism",
            "facttank",
            "pewscience",
            "pewreligion",
            "pewhispanic",
            "pewinternet",
            "pvankessel",
            "justinbieber",
        ]:
            call_command(
                "django_twitter_get_profile", handle, add_to_profile_set="test"
            )
        call_command(
            "django_twitter_get_profile_set_tweets",
            "test",
            num_cores=1,
            ignore_backfill=True,
            limit=25,
            overwrite=True,
        )
        profiles = self.TwitterProfileSet.objects.get(name="test").profiles.all()

        most_similar, most_unique = identify_unusual_profiles_by_tweet_text(profiles)
        self.assertEqual(len(most_unique), 1)
        self.assertEqual(
            self.TwitterProfile.objects.get(
                twitter_id=most_unique["twitter_id"].values[0]
            ).screen_name,
            "justinbieber",
        )

        most_similar, most_unique = identify_unusual_profiles_by_descriptions(profiles)
        self.assertEqual(len(most_unique), 1)
        self.assertEqual(
            self.TwitterProfile.objects.get(
                twitter_id=most_unique["twitter_id"].values[0]
            ).screen_name,
            "justinbieber",
        )

        results = get_monthly_twitter_activity(
            profiles,
            datetime.date(2018, 1, 1),
            max_date=datetime.datetime.now().date() + datetime.timedelta(days=1),
        )
        self.assertEqual(len(results), profiles.count())
        current_month = "{}_{}".format(
            datetime.datetime.now().year, datetime.datetime.now().month
        )
        self.assertIn(current_month, results.columns)
        self.assertGreater(results[current_month].sum(), 0)

        results = find_missing_date_ranges(
            profiles,
            datetime.date(2018, 1, 1),
            max_date=datetime.datetime.now().date() + datetime.timedelta(days=1),
            min_consecutive_missing_dates=1,
        )
        earliest_tweet = (
            self.Tweet.objects.filter(profile__in=profiles)
            .order_by("created_at")[0]
            .created_at
        )
        min_missing = (earliest_tweet - datetime.datetime(2018, 1, 1)).days
        for profile in profiles:
            self.assertGreaterEqual(
                results[results["twitter_id"] == profile.twitter_id]["range"].max(),
                min_missing,
            )

        df = get_twitter_profile_dataframe(
            profiles, datetime.datetime(2018, 1, 1), datetime.datetime.now()
        )
        self.assertEqual(df["date"].min(), datetime.date(2018, 1, 1))
        self.assertEqual(df["date"].max(), datetime.datetime.now().date())
        df = df.dropna(subset=["followers_count"])
        self.assertEqual(profiles.count(), len(df))

        df = get_tweet_dataframe(
            profiles, datetime.datetime(2018, 1, 1), datetime.datetime.now()
        )
        counts = df.groupby("profile")["pk"].count()
        self.assertEqual(profiles.count(), len(counts))

    def test_stream_command(self):

        call_command(
            "django_twitter_collect_tweet_stream",
            num_cores=1,
            limit="1 minute",
            queue_size=5,
            test=True,
        )
        self.assertGreater(self.Tweet.objects.count(), 0)
        self.Tweet.objects.all().delete()

        call_command(
            "django_twitter_collect_tweet_stream",
            num_cores=1,
            limit="10 tweets",
            queue_size=5,
            add_to_profile_set="test",
            add_to_tweet_set="test",
            test=True,
        )
        self.assertGreater(self.Tweet.objects.count(), 0)
        self.assertGreater(self.TweetSet.objects.get(name="test").tweets.count(), 0)
        self.assertGreater(
            self.TwitterProfileSet.objects.get(name="test").profiles.count(), 0
        )

        call_command(
            "django_twitter_collect_tweet_stream",
            num_cores=1,
            limit="1 minute",
            queue_size=5,
            test=True,
            keyword_query="pew",
            add_to_tweet_set="pew_tweets",
        )
        self.assertGreater(
            self.TweetSet.objects.get(name="pew_tweets").tweets.count(), 0
        )

    def tearDown(self):
        from django.conf import settings
        import shutil, os

        cache_path = os.path.join(settings.BASE_DIR, settings.LOCAL_CACHE_ROOT)
        if os.path.exists(cache_path):
            shutil.rmtree(cache_path)
