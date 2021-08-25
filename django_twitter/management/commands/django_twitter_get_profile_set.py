import datetime

from multiprocessing import Pool
from tqdm import tqdm

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django import db

from pewtils import is_null
from django_twitter.utils import get_twitter_profile, get_twitter_profile_set


class Command(BaseCommand):
    """
    Loops over a set of profiles (as defined by an existing TwitterProfileSet's name) and \
    downloads profile data for each profile in the set. Equivalent to looping over the sets \
    in a profile account and running `django_twitter_get_profile`. Supports running these commands \
    in parallel using multiprocessing and the `num_cores` parameter. Multiprocessing is enabled \
    by default and is set to the number of cores.

    :param profile_set: The `name` of the profile set in the database
    :param add_to_profile_set: (Optional) The name of a profile set to add the profiles to. Can be \
    any arbitrary string you want to use; if the profile set doesn't already exist, it will be created. \
    After the command has completed, all of the profiles in the first set should also belong to the second.

    :param api_key: (Optional) Twitter API key, if you don't have the TWITTER_API_KEY environment variable set
    :param api_secret: (Optional) Twitter API secret, if you don't have the TWITTER_API_SECRET environment variable set
    :param access_token: (Optional) Twitter access token, if you don't have the TWITTER_API_ACCESS_TOKEN environment \
    variable set
    :param api_secret: (Optional) Twitter API access secret, if you don't have the TWITTER_API_ACCESS_SECRET \
    environment variable set

    :param num_cores: Number of cores to use in multiprocessing. Defaults to `multiprocessing.cpu_count()`.
    :param collect_all_once: (Optional) If True, this command will attempt to ensure that at least one snapshot \
    has been collected for each profile in the set. On subsequent runs, it will pick up where it left off and will \
    only fetch new snapshots for profiles that do not already have one.

    """

    def add_arguments(self, parser):

        parser.add_argument("profile_set", type=str)
        parser.add_argument("--add_to_profile_set", type=str)

        parser.add_argument("--api_key", type=str)
        parser.add_argument("--api_secret", type=str)
        parser.add_argument("--access_token", type=str)
        parser.add_argument("--access_secret", type=str)

        parser.add_argument("--num_cores", type=int, default=2)
        parser.add_argument("--collect_all_once", action="store_true", default=False)

    def handle(self, *args, **options):

        kwargs = {
            "add_to_profile_set": options["add_to_profile_set"],
            "api_key": options["api_key"],
            "api_secret": options["api_secret"],
            "access_token": options["access_token"],
            "access_secret": options["access_secret"],
        }

        pool = Pool(processes=options["num_cores"])
        profile_set = get_twitter_profile_set(options["profile_set"])
        if options["collect_all_once"]:
            profiles = profile_set.profiles.filter(most_recent_snapshot__isnull=True)
        else:
            profiles = profile_set.profiles.all()
        twitter_ids = profiles.values_list("twitter_id", flat=True)
        for twitter_id in tqdm(twitter_ids, total=len(twitter_ids)):
            if options["num_cores"] > 1:
                pool.apply_async(
                    call_command, ("django_twitter_get_profile", twitter_id), kwargs
                )
            else:
                pool.apply(
                    call_command, ("django_twitter_get_profile", twitter_id), kwargs
                )

        pool.close()
        pool.join()
