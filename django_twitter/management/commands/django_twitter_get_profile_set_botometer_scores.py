import datetime

from multiprocessing import Pool
from tqdm import tqdm

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django import db

from django_twitter.utils import get_twitter_profile, get_twitter_profile_set


class Command(BaseCommand):
    def add_arguments(self, parser):

        parser.add_argument("profile_set", type=str)
        parser.add_argument("--add_to_profile_set", type=str)

        parser.add_argument("--api_key", type=str)
        parser.add_argument("--api_secret", type=str)
        parser.add_argument("--access_token", type=str)
        parser.add_argument("--access_secret", type=str)
        parser.add_argument("--botometer_key", type=str)

        parser.add_argument("--num_cores", type=int, default=2)
        parser.add_argument("--update_existing", action="store_true", default=False)

    def handle(self, *args, **options):

        kwargs = {
            "add_to_profile_set": options["add_to_profile_set"],
            "api_key": options["api_key"],
            "api_secret": options["api_secret"],
            "access_token": options["access_token"],
            "access_secret": options["access_secret"],
            "botometer_key": options["botometer_key"],
        }

        pool = Pool(processes=options["num_cores"])
        profile_set = get_twitter_profile_set(options["profile_set"])
        twitter_ids = profile_set.profiles.values_list("twitter_id", flat=True)
        for twitter_id in tqdm(twitter_ids, total=twitter_ids.count()):
            profile = get_twitter_profile(twitter_id, create=True)
            last_score = profile.most_recent_botometer_score()
            if not last_score or options["update_existing"]:
                if options["num_cores"] > 1:
                    pool.apply_async(
                        call_command,
                        ("django_twitter_get_profile_botometer_score", twitter_id),
                        kwargs,
                    )
                else:
                    pool.apply(
                        call_command,
                        ("django_twitter_get_profile_botometer_score", twitter_id),
                        kwargs,
                    )

        pool.close()
        pool.join()
