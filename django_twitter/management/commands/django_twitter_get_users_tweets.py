from django.conf import settings
from django.core.management.base import BaseCommand
from django.apps import apps
from django.core.management import call_command

from tqdm import tqdm
from multiprocessing.pool import Pool


class Command(BaseCommand):

    def add_arguments(self, parser):

        parser.add_argument("--twitter_ids", nargs="+")
        parser.add_argument("--from_twitter_profile_set", type=str)
        parser.add_argument("--assign_twitter_profile_set", type=str, default=None)

        parser.add_argument("--ignore_backfill", action="store_true", default=False)
        parser.add_argument("--overwrite", action="store_true", default=False)
        parser.add_argument('--max_backfill_date', type=str)

        parser.add_argument('--use_multiprocessing', action='store_true', default=False)
        parser.add_argument("--num_cores", default=2, type=int)

    def handle(self, *args, **options):


        # setup models
        if options["from_twitter_profile_set"]:
            twitter_profile_set_model = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWITTER_PROFILE_SET_MODEL)
            twitter_profile_set, created = twitter_profile_set_model.objects.get_or_create(name=options["from_twitter_profile_set"])
            twitter_ids = list(twitter_profile_set.profiles.all().values_list('twitter_id', flat=True))
        else:
            twitter_ids = options['twitter_ids']

        if not options['use_multiprocessing']:
            for twitter_id in tqdm(twitter_ids, total=len(twitter_ids)):
                _collect_user_tweets(twitter_id, options['assign_twitter_profile_set'])
        else:
            pool = Pool(processes=options['num_cores'])
            for twitter_id in twitter_ids:
                if options['num_cores'] == 1:
                    pool.apply(_collect_user_tweets, args=(twitter_id, options['assign_twitter_profile_set'],
                                                           options["ignore_backfill"], options["overwrite"],
                                                           options["max_backfill_date"]))

                else:
                    pool.apply_async(_collect_user_tweets, args=(twitter_id, options['assign_twitter_profile_set'],
                                                                 options["ignore_backfill"], options["overwrite"],
                                                                 options["max_backfill_date"]))
            pool.close()
            pool.join()

def _collect_user_tweets(twitter_id, assign_twitter_profile_set, ignore_backfill, overwrite, max_backfill_date):
    call_command("django_twitter_get_user", twitter_id, twitter_profile_set= assign_twitter_profile_set)
    call_command("django_twitter_get_user_tweets", twitter_id, no_progress_bar=False,
                 ignore_backfill=ignore_backfill, overwrite=overwrite, max_backfill_date=max_backfill_date,
                 twitter_profile_set=assign_twitter_profile_set)

