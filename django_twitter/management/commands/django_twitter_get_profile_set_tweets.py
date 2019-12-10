from multiprocessing import Pool
from tqdm import tqdm

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django import db

from django_twitter.utils import get_twitter_profile_set


class Command(BaseCommand):
    def add_arguments(self, parser):

        parser.add_argument("profile_set", type=str)
        parser.add_argument("--add_to_profile_set", type=str)
        parser.add_argument("--add_to_tweet_set", type=str)
        parser.add_argument("--ignore_backfill", action="store_true", default=False)
        parser.add_argument("--overwrite", action="store_true", default=False)
        group = parser.add_mutually_exclusive_group(required=False)
        group.add_argument("--max_backfill_date", type=str)
        group.add_argument("--max_backfill_days", type=int)
        parser.add_argument("--no_progress_bar", action="store_true", default=False)
        parser.add_argument("--limit", type=int, default=None)

        parser.add_argument("--api_key", type=str)
        parser.add_argument("--api_secret", type=str)
        parser.add_argument("--access_token", type=str)
        parser.add_argument("--access_secret", type=str)

        parser.add_argument("--num_cores", type=int, default=2)

    def handle(self, *args, **options):

        kwargs = {
            "add_to_profile_set": options["add_to_profile_set"],
            "add_to_tweet_set": options["add_to_tweet_set"],
            "ignore_backfill": options["ignore_backfill"],
            "overwrite": options["overwrite"],
            "max_backfill_date": options["max_backfill_date"],
            "max_backfill_days": options["max_backfill_days"],
            "no_progress_bar": options["no_progress_bar"],
            "limit": options["limit"],
            "api_key": options["api_key"],
            "api_secret": options["api_secret"],
            "access_token": options["access_token"],
            "access_secret": options["access_secret"],
        }

        pool = Pool(processes=options["num_cores"])
        profile_set = get_twitter_profile_set(options["profile_set"])
        twitter_ids = profile_set.profiles.values_list("twitter_id", flat=True)
        for twitter_id in tqdm(twitter_ids, total=len(twitter_ids)):
            if options["num_cores"] > 1:
                pool.apply_async(
                    call_command,
                    ("django_twitter_get_profile_tweets", twitter_id),
                    kwargs,
                )
            else:
                pool.apply(
                    call_command,
                    ("django_twitter_get_profile_tweets", twitter_id),
                    kwargs,
                )

        pool.close()
        pool.join()
