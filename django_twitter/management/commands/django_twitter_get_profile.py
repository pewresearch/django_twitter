from __future__ import print_function
from builtins import str
from django.conf import settings
from django.core.management.base import BaseCommand
from django.apps import apps

from pewhooks.twitter import TwitterAPIHandler

from django_twitter.utils import (
    get_twitter_profile_json,
    get_twitter_profile,
    get_twitter_profile_set,
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

        self.twitter = TwitterAPIHandler(
            api_key=options["api_key"],
            api_secret=options["api_secret"],
            access_token=options["access_token"],
            access_secret=options["access_secret"],
        )

        if options["add_to_profile_set"]:
            profile_set = get_twitter_profile_set(options["add_to_profile_set"])
        else:
            profile_set = None

        print("Collecting profile data for {}".format(options["twitter_id"]))
        twitter_json = get_twitter_profile_json(options["twitter_id"], self.twitter)
        if twitter_json:
            twitter_profile = get_twitter_profile(twitter_json.id_str, create=True)
            twitter_profile.update_from_json(twitter_json._json)
            if profile_set:
                profile_set.profiles.add(twitter_profile)
            print("Successfully saved profile data for {}".format(str(twitter_profile)))