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
        follower, created = user_model.objects.get_or_create(twitter_id=options["twitter_id"])

        # Iterate through all tweets in timeline
        for friend_data in tqdm(self.twitter.iterate_user_friends(options['twitter_id'], hydrate_users=options['hydrate']),
                                desc = "Retrieving friends for user {}".format(follower.screen_name)):
            if not options["hydrate"]:
                friend, created = user_model.objects.get_or_create(twitter_id=friend_data)
            else:
                friend, created = user_model.objects.get_or_create(twitter_id=friend_data._json['id_str'])
                friend.update_from_json(friend_data._json)
            relationship, created = relationship_model.objects.get_or_create(friend=friend, follower=follower)
            date = datetime.datetime.now()
            if date not in relationship.dates:
                relationship.dates.append(date)
                relationship.save()

