import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from django.apps import apps

from pewtils.django import get_model

from tqdm import tqdm

from pewhooks.twitter import TwitterAPIHandler


class Command(BaseCommand):

    def add_arguments(self, parser):

        parser.add_argument("twitter_id", type = str)

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

        scanned_count, updated_count = 0, 0
        user_model = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWITTER_PROFILE_MODEL)
        relationship_model = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWITTER_RELATIONSHIP_MODEL)
        twitter_json = self.twitter.get_user(options["twitter_id"])
        follower, created = user_model.objects.get_or_create(twitter_id=twitter_json.id_str)

        try: run_id = relationship_model.objects.filter(follower=follower).order_by("-run_id")[0].run_id + 1
        except IndexError: run_id = 1

        twitter_profile_set = None
        if options["twitter_profile_set"]:
            twitter_profile_set_model = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWITTER_PROFILE_SET_MODEL)
            twitter_profile_set, created = twitter_profile_set_model.objects.get_or_create(name=options["twitter_profile_set"])

        try:

            # Iterate through all tweets in timeline
            for following_data in tqdm(self.twitter.iterate_user_friends(follower.twitter_id, hydrate_users=options['hydrate']),
                                    desc = "Retrieving friends for user {}".format(follower.screen_name)):
                if not options["hydrate"]:
                    following, created = user_model.objects.get_or_create(twitter_id=following_data)
                else:
                    following, created = user_model.objects.get_or_create(twitter_id=following_data._json['id_str'])
                    following.update_from_json(following_data._json)
                relationship = relationship_model.objects.create(following=following, follower=follower, run_id=run_id)
                # relationship, created = relationship_model.objects.get_or_create(friend=friend, follower=follower)
                # date = datetime.datetime.now()
                # if date not in relationship.dates:
                #     relationship.dates.append(date)
                #     relationship.save()
                if twitter_profile_set:
                    twitter_profile_set.profiles.add(friend)

        except Exception as e:
            print("Encountered an error: {}".format(e))
            relationship_model.objects.filter(follower=follower, run_id=run_id).delete()

