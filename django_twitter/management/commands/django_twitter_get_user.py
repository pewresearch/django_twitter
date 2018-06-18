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

    def handle(self, *args, **options):

        self.twitter = TwitterAPIHandler(
            api_key=options["api_key"],
            api_secret=options["api_secret"],
            access_token=options["access_token"],
            access_secret=options["access_secret"]
        )

        print("Collecting profile data for {}".format(options["twitter_id"]))
        twitter_json = self.twitter.get_user(options["twitter_id"])
        user_model = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWITTER_PROFILE_MODEL)
        twitter_user, created = user_model.objects.get_or_create(twitter_id=options["twitter_id"])
        twitter_user.update_from_json(twitter_json._json)
        print("Successfully saved profile data for {}".format(str(twitter_user)))