from multiprocessing import Pool
from tqdm import tqdm

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django import db

from django_pewtils import reset_django_connection

from django_twitter.utils import safe_get_or_create


class Command(BaseCommand):
    def add_arguments(self, parser):

        parser.add_argument("profile_set", type=str)
        parser.add_argument("--add_to_profile_set", type=str)
        parser.add_argument("--hydrate", action="store_true", default=False)
        parser.add_argument("--limit", type=int)

        parser.add_argument("--api_key", type=str)
        parser.add_argument("--api_secret", type=str)
        parser.add_argument("--access_token", type=str)
        parser.add_argument("--access_secret", type=str)

        parser.add_argument("--num_cores", type=int, default=2)

    def handle(self, *args, **options):

        reset_django_connection()

        kwargs = {
            "add_to_profile_set": options["add_to_profile_set"],
            "hydrate": options["hydrate"],
            "limit": options["limit"],
            "api_key": options["api_key"],
            "api_secret": options["api_secret"],
            "access_token": options["access_token"],
            "access_secret": options["access_secret"],
        }

        pool = Pool(processes=options["num_cores"])
        profile_set = safe_get_or_create(
            "AbstractTwitterProfileSet", "name", options["profile_set"], create=True
        )
        twitter_ids = profile_set.profiles.values_list("twitter_id", flat=True)
        for twitter_id in tqdm(twitter_ids, total=len(twitter_ids)):
            if options["num_cores"] > 1:
                pool.apply_async(
                    call_command,
                    ("django_twitter_get_profile_followers", twitter_id),
                    kwargs,
                )
            else:
                pool.apply(
                    call_command,
                    ("django_twitter_get_profile_followers", twitter_id),
                    kwargs,
                )

        pool.close()
        pool.join()
