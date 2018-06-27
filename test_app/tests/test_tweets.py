from django.test import TestCase
from django.conf import settings
from django.apps import apps
from StringIO import StringIO
from django.core.management import call_command
import sys

# TODO: Figure out how to test this - statuses_count in TwitterProfile is inaccurate
class TweetTest(TestCase):
    def setUp(self):
        self.users = ['nytminuscontext', 'pvankessel', 'michaelbarthel']
        for user in self.users:
            call_command("django_twitter_get_user", user)

    def test_tweets(self):
        for user in self.users:
            call_command("django_twitter_get_user_tweets", user)
            current_user = apps.get_model(app_label=settings.TWITTER_APP,
                                          model_name=settings.TWITTER_PROFILE_MODEL).objects.filter(
                twitter_id=user)
            # if current_user.statuses_count < 3200:
