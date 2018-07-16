from django.test import TransactionTestCase
from django.conf import settings
from django.apps import apps
from django.core.management import call_command


class TestBotometer(TransactionTestCase):
    def setUp(self):
        call_command("django_twitter_get_user_followers", "pankhurikumar23")


    def test_default(self):
        user_model = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWITTER_PROFILE_MODEL).objects.all()

        count = 0
        for user in user_model:
            if count == 30:
                break
            count += 1
            call_command("django_twitter_get_user_botometer_score", user,
                         botometer_key="UjEfOgEaNVmsht9y9cXjHYYQFmpPp1Dpk6ojsnPxPEwluSQFMp")
            print(count)

        botometer_model = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.BOTOMETER_SCORE_MODEL).objects.all()

        self.assertEqual(30, len(botometer_model))

        count = 0
        for score in botometer_model:
            if "error" not in score.json:
                count += 1
                print(count)
                self.assertIsNotNone(score.json["display_scores"]["english"])
                self.assertIsNotNone(score.json["cap"]["english"])

