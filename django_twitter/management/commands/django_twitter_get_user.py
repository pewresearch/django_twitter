from django.conf import settings
from django.core.management.base import BaseCommand

from pewtils.django import get_model

from pewhooks.twitter import TwitterAPIHandler

class Command(BaseCommand):

    def add_arguments(self, parser):

        parser.add_argument("twitter_id", type = str)

    def __init__(self, **options):

        super(Command, self).__init__(**options)
        self.twitter = TwitterAPIHandler()

    def handle(self, *args, **options):

        twitter_json = self.twitter.get_user(options["twitter_id"])

        user_model = get_model(settings.getattr('TWITTER_USER_MODEL'))
        try: twitter_user = user_model.objects.get(twitter_id=options["twitter_id"])
        except user_model.DoesNotExist: twitter_user = user_model.objects.create(twitter_id=options["twitter_id"])

        twitter_user.update_from_json(twitter_json)
