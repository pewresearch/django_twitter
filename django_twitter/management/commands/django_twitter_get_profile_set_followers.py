from django import db
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django_twitter.utils import get_twitter_profile_set, get_concrete_model
from multiprocessing import Pool
from pewtils import is_null
from tqdm import tqdm
import os


class Command(BaseCommand):
    """
    Loops over a set of profiles (as defined by an existing TwitterProfileSet's name) and \
    downloads followers for each profile in the set. Equivalent to looping over the sets \
    in a profile account and running `django_twitter_get_profile_followers`. Supports running these commands \
    in parallel using multiprocessing and the `num_cores` parameter. Multiprocessing is enabled \
    by default and is set to the number of cores.

    :param profile_set: The `name` of the profile set in the database
    :param add_to_profile_set: (Optional) The name of a profile set to add the profiles' followers to. Can be \
    any arbitrary string you want to use; if the profile set doesn't already exist, it will be created.
    :param hydrate: (Optional) By default, this command will only download the Twitter IDs for the profiles' followers. \
    If you pass `hydrate=True`, the command will download the full profile data for each follower, but this requires \
    heavy API usage and can take a long time.
    :param limit: (Optional) Set a limit for the number of followers to collect, for testing purposes. If a limit \
    is passed, `finish_time` will not be set, because the data collection was forcibly aborted.
    :param no_progress_bar: (Optional) Disables the default `tqdm` progress bar.

    :param api_key: (Optional) Twitter API key, if you don't have the TWITTER_API_KEY environment variable set
    :param api_secret: (Optional) Twitter API secret, if you don't have the TWITTER_API_SECRET environment variable set
    :param access_token: (Optional) Twitter access token, if you don't have the TWITTER_API_ACCESS_TOKEN environment \
    variable set
    :param api_secret: (Optional) Twitter API access secret, if you don't have the TWITTER_API_ACCESS_SECRET \
    environment variable set

    :param num_cores: Number of cores to use in multiprocessing. Defaults to `multiprocessing.cpu_count()`.
    :param collect_all_once: (Optional) If True, this command will attempt to ensure that at least one follower list \
    has been collected for each profile in the set. On subsequent runs, it will pick up where it left off and will \
    only fetch new follower lists for profiles that do not already have one.

    """

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
        parser.add_argument("--collect_all_once", action="store_true", default=False)

    def handle(self, *args, **options):

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
        profile_set = get_twitter_profile_set(options["profile_set"])
        if options["collect_all_once"]:
            exclude_profile_ids = (
                get_concrete_model("AbstractTwitterFollowerList")
                .objects.filter(finish_time__isnull=False)
                .filter(profile__in=profile_set.profiles.all())
                .values_list("profile_id", flat=True)
            )
            twitter_ids = profile_set.profiles.exclude(
                pk__in=exclude_profile_ids
            ).values_list("twitter_id", flat=True)
        else:
            twitter_ids = profile_set.profiles.values_list("twitter_id", flat=True)
        for twitter_id in tqdm(twitter_ids, total=len(twitter_ids), disable=os.environ.get("DISABLE_TQDM", False)):
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
