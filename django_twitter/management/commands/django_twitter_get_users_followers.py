import datetime, hashlib

from django.conf import settings
from django.core.management.base import BaseCommand
from django.apps import apps
from django.core.management import call_command

from pewtils.django import get_model

from tqdm import tqdm

from pewhooks.twitter import TwitterAPIHandler


class Command(BaseCommand):

    def add_arguments(self, parser):

        parser.add_argument("twitter_profile_set", type=str)

        parser.add_argument("--hydrate", action="store_true", default=False)
        parser.add_argument("--twitter_profile_set", type=str)
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

        twitter_profile_set_model = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWITTER_PROFILE_SET_MODEL)
        twitter_profile_set, created = twitter_profile_set_model.objects.get_or_create(name=options["twitter_profile_set"])

        for twitter_profile in twitter_profile_set.profiles.chunk(100):
            call_command('django_twitter_get_user_followers', twitter_profile.twitter_id,
                         api_key=self.twitter.api_key,
                         api_secret=self.twitter.api_secret,
                         access_token=self.twitter.access_token,
                         access_secret=self.twitter.access_secret)
            # by passing along the current active api key, any cycling between multiple keys will be propagated to the subcommands

