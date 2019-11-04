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


class BaseTests(DjangoTestCase):

    """
    To test, navigate to django_twitter root folder and run `python manage.py test testapp.tests`
    """

    def setUp(self):

        self.TwitterProfile = apps.get_model(
            app_label=settings.TWITTER_APP, model_name=settings.TWITTER_PROFILE_MODEL
        )
        self.TwitterProfileSet = apps.get_model(
            app_label=settings.TWITTER_APP,
            model_name=settings.TWITTER_PROFILE_SET_MODEL,
        )
        self.Tweet = apps.get_model(
            app_label=settings.TWITTER_APP, model_name=settings.TWEET_MODEL
        )
        self.TweetSet = apps.get_model(
            app_label=settings.TWITTER_APP, model_name=settings.TWEET_SET_MODEL
        )
        self.BotometerScore = apps.get_model(
            app_label=settings.TWITTER_APP, model_name=settings.BOTOMETER_SCORE_MODEL
        )
        self.TwitterRelationship = apps.get_model(
            app_label=settings.TWITTER_APP,
            model_name=settings.TWITTER_RELATIONSHIP_MODEL,
        )
        self.TwitterHashtag = apps.get_model(
            app_label=settings.TWITTER_APP, model_name=settings.TWITTER_HASHTAG_MODEL
        )

    def test_user_commands(self):

        call_command(
            "django_twitter_get_profile", "pvankessel", add_to_profile_set="get_profile"
        )
        self.assertEqual(
            self.TwitterProfile.objects.filter(screen_name="pvankessel").count(), 1
        )
        profile = self.TwitterProfile.objects.get(screen_name="pvankessel")
        profile.json = json.dumps(profile.json)
        profile.save()
        profile.update_from_json()
        self.assertIsNotNone(profile.twitter_id)
        self.assertIsNotNone(profile.created_at)
        self.assertIsNotNone(profile.followers_count)
        self.assertIsNotNone(profile.description)
        self.assertIsNotNone(profile.favorites_count)
        self.assertIsNotNone(profile.screen_name)

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
        self.assertGreater(profile.followers.count(), 0)
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
        self.assertGreater(profile.followings.count(), 0)
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

        call_command(
            "django_twitter_get_profile_botometer_score",
            profile.twitter_id,
            add_to_profile_set="get_profile_botometer_score",
        )
        self.assertGreater(profile.botometer_scores.count(), 0)
        score = profile.most_recent_botometer_score()
        self.assertIsNotNone(score.json["cap"]["english"])
        self.assertIsNotNone(score.json["display_scores"]["english"])
        self.assertIsNotNone(score.overall_score_english)

        call_command(
            "django_twitter_get_profile_set_botometer_scores",
            "get_profile_botometer_score",
            num_cores=1,
            add_to_profile_set="get_profile_set_botometer_scores",
            update_existing=True,  # so we fetch it again and link the profile to the profile set correctly
        )
        self.assertEqual(
            profile.twitter_profile_sets.filter(
                name="get_profile_set_botometer_scores"
            ).count(),
            1,
        )

        self.assertGreater(self.TwitterProfile.objects.count(), 0)
        self.assertGreater(self.TwitterRelationship.objects.count(), 0)
        self.assertGreater(self.TwitterHashtag.objects.count(), 0)

    def test_utility_functions(self):

        from django_twitter.utils import (
            identify_unusual_profiles_by_descriptions,
            identify_unusual_profiles_by_tweet_text,
            get_monthly_twitter_activity,
            find_missing_date_ranges,
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
