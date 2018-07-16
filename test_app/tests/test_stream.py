from django.test import TransactionTestCase
from django.conf import settings
from django.apps import apps
from find_path import get_recursively

from django.core.management import call_command
import random


class TestStream(TransactionTestCase):
    def setUp(self):
        # TODO: unicode, single core, "OR" testing
        self.option_tests = [[100, 2, "1000 tweets", None, None],
                             [500, 4, "1000 tweets", None, None],
                             [500, 2, "1000 tweets", "testing123", None],
                             [500, 2, "1000 tweets", False, "supreme"],
                             [50, 2, "1000 tweets", "testing123", "france belgium semi final"],
                             [500, 2, "1000 tweets", False, "france OR belgium"],
                             [500, 2, "1000 tweets", False, "match #frabel"]]

    def test_stream_basic(self):
        for item in self.option_tests:
            call_command("flush", noinput=True)

            call_command("django_twitter_collect_tweet_stream", queue_size=item[0],
                         num_cores=item[1], limit=item[2], tweet_set=item[3], keyword_query=item[4])

            self.push_assert(item)
            # self.find_path()

        # print(len(tweets))

    def push_assert(self, item):
        tweets = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWEET_MODEL).objects.all()

        # verify number of tweets
        print(len(tweets))
        self.assertTrue(900 <= len(tweets) <= 1000)

        if item[3]:
            for tweet in tweets:
                s = tweet.tweet_sets.all()
                if len(s) > 0:
                    self.assertEqual(len(s), 1)
                    s0 = s.first()
                    self.assertEqual(s0.name, item[3])

        # verify information
        for i in range(20):
            idx = random.randint(0, len(tweets) - 1)
            self.assertIsNotNone(tweets[idx].twitter_id)
            self.assertIsNotNone(tweets[idx].text)
            self.assertIsNotNone(tweets[idx].created_at)
            self.assertIsNotNone(tweets[idx].retweeted)
            self.assertIsNotNone(tweets[idx].profile)
            # verify keyword(s)
            if item[4] is not None:
                lst_search = item[4].split(" ")
                self.text1 = ""
                text2 = ""
                if 'extended_tweet' in tweets[idx].json:
                    print("A")
                    self.text1 = tweets[idx].json['extended_tweet']['full_text'].lower()
                elif 'retweeted_status' in tweets[idx].json:
                    if 'extended_tweet' in tweets[idx].json['retweeted_status']:
                        print("B")
                        self.text1 = tweets[idx].json['retweeted_status']['extended_tweet']['full_text'].lower()
                    if 'quoted_status' in tweets[idx].json['retweeted_status']:
                        if 'extended_tweet' in tweets[idx].json['retweeted_status']['quoted_status']:
                            print("C")
                            text2 = tweets[idx].json['retweeted_status']['quoted_status']['extended_tweet']['full_text'].lower()
                        else:
                            print("D")
                            text2 = tweets[idx].json['retweeted_status']['quoted_status']['text'].lower()
                    else:
                        print("G")
                        self.text1 = tweets[idx].json['retweeted_status']['text']
                elif 'quoted_status' in tweets[idx].json:
                    if 'extended_tweet' in tweets[idx].json['quoted_status']:
                        print("H")
                        text2 = tweets[idx].json['quoted_status']['extended_tweet']['full_text'].lower()
                    else:
                        print("I")
                        text2 = tweets[idx].json['quoted_status']['text'].lower()
                else:
                    print("J")
                    self.text1 = tweets[idx].json['text'].lower()
                # print(self.text1)
                # print(text2)
                for elt in lst_search:
                    if self.text1 != "":
                        try:
                            self.assertIn(elt, self.text1)
                        except AssertionError:
                            if text2 != "":
                                self.assertIn(elt, text2)
                    else:
                        print(self.text1)
                        print(text2)
                        self.assertIn(elt, text2)

    # Finding "full_text" path for storing/testing tweets
    def find_path(self):
        results = []
        tweets = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWEET_MODEL).objects.all()
        for tweet in tweets:
            value, path = get_recursively(tweet.json, 'full_text')
            if path not in results:
                print('\n\n\n\n')
                print(tweet.json)
                print(path)
                results.append(path)
        print(results)
