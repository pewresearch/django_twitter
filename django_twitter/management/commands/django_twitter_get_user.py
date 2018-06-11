from django.conf import settings
from django.core.management.base import BaseCommand
from django.apps import apps


from pewhooks.twitter import TwitterAPIHandler

class Command(BaseCommand):

    def add_arguments(self, parser):

        parser.add_argument("twitter_id", type = str)

    def __init__(self, **options):

        super(Command, self).__init__(**options)
        self.twitter = TwitterAPIHandler()

    def handle(self, *args, **options):

        twitter_json = self.twitter.get_user(options["twitter_id"])

        user_model = apps.get_model(app_label="test_app", model_name=settings.TWITTER_PROFILE_MODEL)
        import pdb
        pdb.set_trace()
        try: twitter_user = user_model.objects.get(twitter_id=options["twitter_id"])
        except user_model.DoesNotExist: twitter_user = user_model.objects.create(twitter_id=options["twitter_id"])

        twitter_user.update_from_json(twitter_json)
