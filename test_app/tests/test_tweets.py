from __future__ import absolute_import
from django.test import TestCase
from django.conf import settings
from django.apps import apps
from django.core.management import call_command
import json
from .find_path import get_recursively

# TODO: Figure out how to test this - statuses_count in TwitterProfile is inaccurate
# class TweetTest(TestCase):
#     def setUp(self):
#         self.users = ['pvankessel']#, 'pankhurikumar23']
#         for user in self.users:
#             call_command("django_twitter_get_user_tweets", user)
#
#     def test_tweets(self):
#         tweets = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWEET_MODEL).objects.all()
#
#         results = []
#
#         for tweet in tweets:
#             value, path = get_recursively(tweet.json, )
