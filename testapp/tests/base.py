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

        self.TwitterProfile = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWITTER_PROFILE_MODEL)
        self.TwitterProfileSet = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWITTER_PROFILE_SET_MODEL)
        self.Tweet = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWEET_MODEL)
        self.TweetSet = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWEET_SET_MODEL)
        self.BotometerScore = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.BOTOMETER_SCORE_MODEL)
        self.TwitterRelationship = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWITTER_RELATIONSHIP_MODEL)
        self.TwitterHashtag = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWITTER_HASHTAG_MODEL)

    def test_user_commands(self):

        call_command('django_twitter_get_user', "pvankessel")
        self.assertEqual(self.TwitterProfile.objects.filter(screen_name="pvankessel").count(), 1)
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

        call_command('django_twitter_get_user_followers', profile.twitter_id)
        self.assertGreater(profile.followers.count(), 0)
        self.assertGreater(profile.current_followers().count(), 0)

        call_command('django_twitter_get_user_following', profile.twitter_id)
        self.assertGreater(profile.followings.count(), 0)
        self.assertGreater(profile.current_followings().count(), 0)
        call_command('django_twitter_get_user_tweets', profile.twitter_id, limit=50, tweet_set_name="test")
        correct_num_tweets = profile.tweets.count()
        self.assertGreater(correct_num_tweets, 0)
        for tweet in self.TweetSet.objects.get(name="test").tweets.all()[:5]:
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
        call_command('django_twitter_get_user_tweets', profile.twitter_id, ignore_backfill=True, max_backfill_date=limit1.strftime("%Y-%m-%d"), limit=50)
        self.assertGreater(profile.tweets.count(), num_tweets)
        num_tweets = profile.tweets.count()
        self.assertLess(num_tweets, correct_num_tweets)
        call_command('django_twitter_get_user_tweets', profile.twitter_id, ignore_backfill=True, limit=50)
        self.assertGreaterEqual(profile.tweets.count(), correct_num_tweets)

        call_command('django_twitter_get_user_botometer_score', profile.twitter_id)
        self.assertGreater(profile.botometer_scores.count(), 0)
        score = profile.most_recent_botometer_score()
        self.assertIsNotNone(score.json['cap']['english'])
        self.assertIsNotNone(score.json['display_scores']['english'])
        self.assertIsNotNone(score.overall_score_english)

        self.assertGreater(self.TwitterProfile.objects.count(), 0)
        self.assertGreater(self.TwitterRelationship.objects.count(), 0)
        self.assertGreater(self.TwitterHashtag.objects.count(), 0)

    def test_stream_command(self):

        call_command('django_twitter_collect_tweet_stream', num_cores=1, limit="1 minute", queue_size=5, test=True)
        self.assertGreater(self.Tweet.objects.count(), 0)
        self.Tweet.objects.all().delete()
        call_command('django_twitter_collect_tweet_stream', num_cores=1, limit="10 tweets", queue_size=5,
                     profile_set_name="test", tweet_set_name="test", test=True)
        self.assertGreater(self.Tweet.objects.count(), 0)
        self.assertGreater(self.TweetSet.objects.get(name="test").tweets.count(), 0)
        self.assertGreater(self.TwitterProfileSet.objects.get(name="test").profiles.count(), 0)

    def tearDown(self):
        pass