from django.test import TransactionTestCase
from django.conf import settings
from django.apps import apps

from StringIO import StringIO
from django.core.management import call_command
import sys

import django_twitter.management.commands.django_twitter_collect_tweet_stream as stream


class TestStream(TransactionTestCase):
    def setUp(self):
        call_command("flush", noinput=True)

    # def test_stream_basic(self):
    #     # cores = 1
    #     # queue_size = 100
    #     # tweet_set = False
    #     saved_stdout = sys.stdout
    #     sys.stdout = out = StringIO()
    #     call_command("django_twitter_collect_tweet_stream", queue_size=100, num_cores=1, stdout=out)
    #     tweets = apps.get_model(app_label=settings.TWITTER_APP,
    #                             model_name=settings.TWEET_MODEL).objects.all()
    #     self.assertIn(str(len(tweets)), out.getvalue())
    #
    #     sys.stdout = saved_stdout
    #     out.close()
    #     print(len(tweets))

    # def test_stream_cores(self):
    #     # cores = 4
    #     # queue_size = 100
    #     # tweet_set = False
    #     saved_stdout = sys.stdout
    #     sys.stdout = out = StringIO()
    #     call_command("django_twitter_collect_tweet_stream", queue_size=100, num_cores=4, stdout=out)
    #     tweets = apps.get_model(app_label=settings.TWITTER_APP,
    #                             model_name=settings.TWEET_MODEL).objects.all()
    #     self.assertIn(str(len(tweets)), out.getvalue())
    #
    #     sys.stdout = saved_stdout
    #     out.close()
    #     print(len(tweets))

    def test_stream_tweetset(self):
        # cores = 2, default
        # queue_size = 500, default
        # tweet_set = True
        saved_stdout = sys.stdout
        sys.stdout = out = StringIO()
        call_command("django_twitter_collect_tweet_stream", tweet_set="testset", stdout=out)
        tweets = apps.get_model(app_label=settings.TWITTER_APP,
                                model_name=settings.TWEET_SET_MODEL).objects.filter(name="testset")
        # print(len(tweets))
        self.assertIn(str(len(tweets)), out.getvalue())

        sys.stdout = saved_stdout
        out.close()
