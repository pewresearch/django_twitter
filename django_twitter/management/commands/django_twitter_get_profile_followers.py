from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from pewhooks.twitter import TwitterAPIHandler
from tqdm import tqdm
import datetime
import os
from django_twitter.utils import (
    get_twitter_profile_json,
    get_twitter_profile,
    get_twitter_profile_set,
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

        self.twitter = TwitterAPIHandler(
            api_key=options["api_key"],
            api_secret=options["api_secret"],
            access_token=options["access_token"],
            access_secret=options["access_secret"],
        )

        TwitterFollowerList = get_concrete_model("AbstractTwitterFollowerList")

        if options["add_to_profile_set"]:
            profile_set = get_twitter_profile_set(options["add_to_profile_set"])
        else:
            profile_set = None

        twitter_json = get_twitter_profile_json(options["twitter_id"], self.twitter)
        if twitter_json:

            profile = get_twitter_profile(twitter_json.id_str, create=True)
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
                        follower = get_twitter_profile(follower_data, create=True)
                    else:
                        follower = get_twitter_profile(
                            follower_data._json["id_str"], create=True
                        )
                        follower.update_from_json(follower_data._json)
                    follower_list.followers.add(follower)
                    if profile_set:
                        profile_set.profiles.add(follower)

                follower_list.finish_time = datetime.datetime.now()
                follower_list.save()

            except Exception as e:
                print("Encountered an error: {}".format(e))
                follower_list.delete()
