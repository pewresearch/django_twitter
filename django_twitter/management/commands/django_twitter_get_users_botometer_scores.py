from django.conf import settings
from django.core.management.base import BaseCommand
from django.apps import apps
from django.core.management import call_command
from multiprocessing import Pool
from django import db

from datetime import datetime
from tqdm import tqdm


class Command(BaseCommand):

    def add_arguments(self, parser):

        parser.add_argument("--twitter_ids", nargs="+")
        parser.add_argument("--num_cores", type=int, default=2)

        parser.add_argument("--twitter_profile_set", type=str)
        parser.add_argument('--botometer_key', type=str)
        parser.add_argument('--update', action='store_true', default=False)

    def handle(self, *args, **options):

        # setup models
        twitter_profile_model = apps.get_model(app_label=settings.TWITTER_APP,
                                               model_name=settings.TWITTER_PROFILE_MODEL)
        if options["twitter_profile_set"]:
            twitter_profile_set_model = apps.get_model(app_label=settings.TWITTER_APP,
                                                       model_name=settings.TWITTER_PROFILE_SET_MODEL)
            twitter_profile_set, created = twitter_profile_set_model.objects.get_or_create(
                name=options["twitter_profile_set"])
            twitter_ids = list(twitter_profile_set.profiles.all().values_list('twitter_id', flat=True))
        else:
            twitter_ids = options['twitter_ids']

        for twitter_id in tqdm(twitter_ids, total=len(twitter_ids)):
            user = twitter_profile_model.objects.get(twitter_id=twitter_id)
            last_score = user.most_recent_botometer_score()
            if not last_score:
                run_command = True
            else:
                if options['update']:
                    if last_score.timestamp.date() == datetime.now().date():
                        run_command = False
                    else:
                        run_command = True
                else:
                    run_command = False

            if run_command:
                _get_score(twitter_id, options['botometer_key'], options['num_cores'])


def _get_score(twitter_id, key, num_cores):
    pool = Pool(processes=num_cores)

    if num_cores > 1:
        pool.apply_async(_get_botometer_score, args=(twitter_id, key))
    else:
        pool.apply(_get_botometer_score, args=[twitter_id, key])

    pool.close()
    pool.join()
    db.connections.close_all()


def _get_botometer_score(twitter_id, key):
    call_command("django_twitter_get_user_botometer_score", twitter_id, botometer_key=key)
