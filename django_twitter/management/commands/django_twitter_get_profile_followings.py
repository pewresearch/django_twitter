from __future__ import print_function

import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from django.apps import apps

from tqdm import tqdm

from pewhooks.twitter import TwitterAPIHandler
from django_pewtils import reset_django_connection

from django_twitter.utils import (
    get_twitter_profile_json,
    safe_get_or_create,
    get_concrete_model,
)


class Command(BaseCommand):
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

        TwitterFollowingList = get_concrete_model("AbstractTwitterFollowingList")

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
            following_list = TwitterFollowingList.objects.create(profile=profile)

            try:

                # Iterate through all tweets in timeline
                iterator = self.twitter.iterate_profile_followings(
                    profile.twitter_id,
                    hydrate_profiles=options["hydrate"],
                    limit=options["limit"],
                )

                if not options["no_progress_bar"]:
                    iterator = tqdm(
                        iterator,
                        desc="Retrieving friends for user {}".format(
                            profile.screen_name
                        ),
                    )

                for following_data in iterator:
                    if not options["hydrate"]:
                        following = safe_get_or_create(
                            "AbstractTwitterProfile",
                            "twitter_id",
                            following_data,
                            create=True,
                        )
                    else:
                        following = safe_get_or_create(
                            "AbstractTwitterProfile",
                            "twitter_id",
                            following_data._json["id_str"],
                            create=True,
                        )
                        snapshot = get_concrete_model(
                            "AbstractTwitterProfileSnapshot"
                        ).objects.create(profile=following)
                        snapshot.update_from_json(following_data._json)
                    following_list.followings.add(following)
                    if profile_set:
                        profile_set.profiles.add(following)

                following_list.finish_time = datetime.datetime.now()
                following_list.save()

            except Exception as e:
                print("Encountered an error: {}".format(e))
                following_list.delete()
