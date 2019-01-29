from __future__ import print_function
from builtins import str
from django.conf import settings
from django.core.management.base import BaseCommand
from django.apps import apps

from pewhooks.twitter import TwitterAPIHandler

from django_twitter.utils import get_twitter_user


class Command(BaseCommand):

    def add_arguments(self, parser):

        parser.add_argument("twitter_id", type = str)

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

        twitter_profile_set = None
        if options["twitter_profile_set"]:
            twitter_profile_set_model = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWITTER_PROFILE_SET_MODEL)
            twitter_profile_set, created = twitter_profile_set_model.objects.get_or_create(name=options["twitter_profile_set"])

        print("Collecting profile data for {}".format(options["twitter_id"]))
        twitter_json = get_twitter_user(options["twitter_id"], self.twitter)
        if twitter_json:
            user_model = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWITTER_PROFILE_MODEL)
            twitter_user, created = user_model.objects.get_or_create(twitter_id=twitter_json.id)
            twitter_user.update_from_json(twitter_json._json)
            if twitter_profile_set:
                twitter_profile_set.profiles.add(twitter_user)
            print("Successfully saved profile data for {}".format(str(twitter_user)))
