from __future__ import print_function

import datetime
import os

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand

from tqdm import tqdm

from pewhooks.twitter import TwitterAPIHandler

from django_twitter.utils import (
    get_twitter_profile_json,
    safe_get_or_create,
    get_concrete_model,
)


class Command(BaseCommand):
    """
    Download and save a Twitter account's followers.

    :param twitter_id: The unique Twitter ID for the account
    :param add_to_profile_set: (Optional) The name of a profile set to add the followers to. Can be \
    any arbitrary string you want to use; if the profile set doesn't already exist, it will be created
    :param hydrate: (Optional) By default, this command will only download the Twitter IDs for the profile's followers. \
    If you pass `hydrate=True`, the command will download the full profile data for each follower, but this requires \
    heavy API usage and can take a long time.
    :param limit: (Optional) Set a limit for the number of followers to collect, for testing purposes. If a limit \
    is passed, `finish_time` will not be set, because the data collection was forcibly aborted.
    :param no_progress_bar: (Optional) Disables the default `tqdm` progress bar.

    :param api_key: (Optional) Twitter API key, if you don't have the TWITTER_API_KEY environment variable set
    :param api_secret: (Optional) Twitter API secret, if you don't have the TWITTER_API_SECRET environment variable set
    :param access_token: (Optional) Twitter access token, if you don't have the TWITTER_API_ACCESS_TOKEN environment \
    variable set
    :param access_secret: (Optional) Twitter API access secret, if you don't have the TWITTER_API_ACCESS_SECRET \
    environment variable set
    """

    def add_arguments(self, parser):

        parser.add_argument("twitter_id", type=str)
        parser.add_argument("--add_to_profile_set", type=str)
        parser.add_argument("--hydrate", action="store_true", default=False)
        parser.add_argument("--limit", type=int)
        parser.add_argument("--no_progress_bar", action="store_true", default=False)

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

        TwitterFollowerList = get_concrete_model("AbstractTwitterFollowerList")

        if options["add_to_profile_set"]:
            profile_set = safe_get_or_create(
                "AbstractTwitterProfileSet",
                "name",
                options["add_to_profile_set"],
                create=True,
            )
        else:
            profile_set = None

        twitter_json = get_twitter_profile_json(options["twitter_id"], self.twitter)
        if twitter_json:

            profile = safe_get_or_create(
                "AbstractTwitterProfile", "twitter_id", twitter_json.id_str, create=True
            )
            profile.twitter_error_code = None
            profile.save()
            follower_list = TwitterFollowerList.objects.create(profile=profile)

            try:

                # Iterate through all tweets in timeline
                iterator = self.twitter.iterate_profile_followers(
                    profile.twitter_id,
                    hydrate_profiles=options["hydrate"],
                    limit=options["limit"],
                )

                if not options["no_progress_bar"]:
                    iterator = tqdm(
                        iterator,
                        desc="Retrieving followers for user {}".format(
                            profile.screen_name
                        ), disable=os.environ.get("DISABLE_TQDM", False),
                    )

                for follower_data in iterator:
                    if not options["hydrate"]:
                        follower = safe_get_or_create(
                            "AbstractTwitterProfile",
                            "twitter_id",
                            follower_data,
                            create=True,
                        )
                    else:
                        follower = safe_get_or_create(
                            "AbstractTwitterProfile",
                            "twitter_id",
                            follower_data._json["id_str"],
                            create=True,
                        )
                        snapshot = get_concrete_model(
                            "AbstractTwitterProfileSnapshot"
                        ).objects.create(profile=follower)
                        snapshot.update_from_json(follower_data._json)
                    follower_list.followers.add(follower)
                    if profile_set:
                        profile_set.profiles.add(follower)

                if not options["limit"]:
                    follower_list.finish_time = datetime.datetime.now()
                follower_list.save()

            except Exception as e:
                print("Encountered an error: {}".format(e))
                follower_list.delete()
