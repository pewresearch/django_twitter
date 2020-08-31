from __future__ import print_function

from django.conf import settings
from django.core.management.base import BaseCommand
from django.apps import apps

from tqdm import tqdm

from pewhooks.twitter import TwitterAPIHandler

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

        TwitterRelationship = get_concrete_model("AbstractTwitterRelationship")

        if options["add_to_profile_set"]:
            profile_set = get_twitter_profile_set(options["add_to_profile_set"])
        else:
            profile_set = None

        twitter_json = get_twitter_profile_json(options["twitter_id"], self.twitter)
        if twitter_json:

            following = get_twitter_profile(twitter_json.id_str, create=True)
            snapshot = get_concrete_model(
                "AbstractTwitterProfileSnapshot"
            ).objects.create(profile=following)
            snapshot.update_from_json(twitter_json._json)
            try:
                run_id = (
                    TwitterRelationship.objects.filter(following=following)
                    .order_by("-run_id")[0]
                    .run_id
                    + 1
                )
            except IndexError:
                run_id = 1

            try:

                # Iterate through all tweets in timeline
                iterator = self.twitter.iterate_profile_followers(
                    following.twitter_id,
                    hydrate_profiles=options["hydrate"],
                    limit=options["limit"],
                )

                if not options["no_progress_bar"]:
                    iterator = tqdm(
                        iterator,
                        desc="Retrieving followers for user {}".format(
                            following.screen_name
                        ),
                    )

                for follower_data in iterator:
                    if not options["hydrate"]:
                        follower = get_twitter_profile(follower_data, create=True)
                    else:
                        follower = get_twitter_profile(
                            follower_data._json["id_str"], create=True
                        )
                        follower.update_from_json(follower_data._json)
                    relationship = TwitterRelationship.objects.create(
                        following=following, follower=follower, run_id=run_id
                    )
                    if profile_set:
                        profile_set.profiles.add(follower)

            except Exception as e:
                print("Encountered an error: {}".format(e))
                TwitterRelationship.objects.filter(
                    following=following, run_id=run_id
                ).delete()
