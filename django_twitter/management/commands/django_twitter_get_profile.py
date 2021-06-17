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
    """
    Download and save data for a Twitter profile.

    :param twitter_id: The profile's unique Twitter ID (or, if it's the first time you're downloading data for this \
    profile and you don't know the Twitter ID, you can pass a screen name)
    :param add_to_profile_set: (Optional) The name of a profile set to add the profile to. Can be \
    any arbitrary string you want to use; if the profile set doesn't already exist, it will be created
    :param api_key: (Optional) Twitter API key, if you don't have the TWITTER_API_KEY environment variable set
    :param api_secret: (Optional) Twitter API secret, if you don't have the TWITTER_API_SECRET environment variable set
    :param access_token: (Optional) Twitter access token, if you don't have the TWITTER_API_ACCESS_TOKEN environment \
    variable set
    :param api_secret: (Optional) Twitter API access secret, if you don't have the TWITTER_API_ACCESS_SECRET \
    environment variable set
    """

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
