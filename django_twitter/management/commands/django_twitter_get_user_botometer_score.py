from django.conf import settings
from django.core.management.base import BaseCommand
from django.apps import apps


from pewhooks.twitter import TwitterAPIHandler

class Command(BaseCommand):

    def add_arguments(self, parser):

        parser.add_argument("twitter_id", type = str)

        parser.add_argument('--api_key', type=str)
        parser.add_argument('--api_secret', type=str)
        parser.add_argument('--access_token', type=str)
        parser.add_argument('--access_secret', type=str)
        parser.add_argument('--botometer_key', type=str)

    def handle(self, *args, **options):

        self.twitter = TwitterAPIHandler(
            api_key=options["api_key"],
            api_secret=options["api_secret"],
            access_token=options["access_token"],
            access_secret=options["access_secret"],
            botometer_key=options["botometer_key"]
        )

        user_model = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWITTER_PROFILE_MODEL)
        twitter_user, created = user_model.objects.get_or_create(twitter_id=options["twitter_id"])

        botometer_scores = self.twitter.get_user_botometer_score(options["twitter_id"])
        botometer_model = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.BOTOMETER_SCORE_MODEL)
        score = botometer_model.objects.create(profile=twitter_user)
        score.update_from_json(botometer_scores)