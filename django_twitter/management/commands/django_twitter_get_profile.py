from __future__ import print_function
from builtins import str
from django.conf import settings
from django.core.management.base import BaseCommand
from django.apps import apps

from pewhooks.twitter import TwitterAPIHandler
from django_pewtils import reset_django_connection

from django_twitter.utils import (
    get_concrete_model,
    get_twitter_profile_json,
    safe_get_or_create,
)


class Command(BaseCommand):
    def add_arguments(self, parser):

        parser.add_argument("twitter_id", type=str)
        parser.add_argument("--add_to_profile_set", type=str)

        parser.add_argument("--api_key", type=str)
        parser.add_argument("--api_secret", type=str)
        parser.add_argument("--access_token", type=str)
        parser.add_argument("--access_secret", type=str)

    def handle(self, *args, **options):

        reset_django_connection()

        self.twitter = TwitterAPIHandler(
            api_key=options["api_key"],
            api_secret=options["api_secret"],
            access_token=options["access_token"],
            access_secret=options["access_secret"],
        )

        if options["add_to_profile_set"]:
            profile_set = safe_get_or_create(
                "AbstractTwitterProfileSet",
                "name",
                options["add_to_profile_set"],
                create=True,
            )
        else:
            profile_set = None

        print("Collecting profile data for {}".format(options["twitter_id"]))
        twitter_json = get_twitter_profile_json(options["twitter_id"], self.twitter)
        if twitter_json:
            twitter_profile = safe_get_or_create(
                "AbstractTwitterProfile", "twitter_id", twitter_json.id_str, create=True
            )
            snapshot = get_concrete_model(
                "AbstractTwitterProfileSnapshot"
            ).objects.create(profile=twitter_profile)
            snapshot.update_from_json(twitter_json._json)
            twitter_profile.twitter_error_code = None
            twitter_profile.save()
            if profile_set:
                profile_set.profiles.add(twitter_profile)
            print("Successfully saved profile data for {}".format(str(twitter_profile)))
