from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.apps import apps

from tqdm import tqdm

from pewhooks.twitter import TwitterAPIHandler

class Command(BaseCommand):

    def add_arguments(self, parser):

        parser.add_argument("-d", "--debug", action="store_true")
        parser.add_argument("-l", "--long", action="store_false")

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

        # setup
        if options["debug"]:
            import pdb
            pdb.set_trace()
        if options["long"]:
            max_users=500
        else:
            max_users=50

        # collect users
        lst_test_users = []
        all_users = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWITTER_PROFILE_MODEL).objects.all()
        for user in all_users[:max_users]:
            if not user.screen_name: lst_test_users.append(user.id)

        # start testing
        print("Testing {} users".format(len(lst_test_users)))
        call_command('django_twitter_get_user_tweets', lst_test_users)
