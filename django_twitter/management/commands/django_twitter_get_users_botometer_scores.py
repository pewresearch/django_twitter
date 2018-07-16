from django.conf import settings
from django.core.management.base import BaseCommand
from django.apps import apps
from django.core.management import call_command

from tqdm import tqdm


class Command(BaseCommand):

    def add_arguments(self, parser):

        parser.add_argument("--twitter_ids", nargs="+")

        parser.add_argument("--twitter_profile_set", type=str)
        parser.add_argument('--botometer_key', type=str)

    def handle(self, *args, **options):



        # setup models
        if options["twitter_profile_set"]:
            twitter_profile_set_model = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWITTER_PROFILE_SET_MODEL)
            twitter_profile_set, created = twitter_profile_set_model.objects.get_or_create(name=options["twitter_profile_set"])
            twitter_ids = list(twitter_profile_set.profiles.all().values_list('twitter_id', flat=True))
        else:
            twitter_ids = options['twitter_ids']

        for twitter_id in tqdm(twitter_ids, total=len(twitter_ids)):
            call_command("django_twitter_get_user_botometer_score", twitter_id, botometer_key=options['botometer_key'])
