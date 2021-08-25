from multiprocessing import Pool
from tqdm import tqdm

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django import db
from django.db.models import Count

from pewtils import is_null
from django_twitter.utils import get_twitter_profile_set


class Command(BaseCommand):
    """
    Loops over a set of profiles (as defined by an existing TwitterProfileSet's name) and \
    downloads tweets for each profile in the set. Equivalent to looping over the sets \
    in a profile account and running `django_twitter_get_profile_tweets`. Supports running these commands \
    in parallel using multiprocessing and the `num_cores` parameter. Multiprocessing is enabled \
    by default and is set to the number of cores.

    :param profile_set: The `name` of the profile set in the database
    :param add_to_profile_set: (Optional) The name of a profile set to add the profiles to. Can be \
    any arbitrary string you want to use; if the profile set doesn't already exist, it will be created. \
    After the command has completed, all of the profiles in the first set should also belong to the second.

    :param add_to_tweet_set: (Optional) The name of a tweet set to add each tweet to. Can be \
    any arbitrary string you want to use; if the tweet set doesn't already exist, it will be created.
    :param ignore_backfill: (Optional) By default, Django Twitter will only iterate through a profile's full tweet \
    timeline the first time it runs. Once it has successfully iterated through all of a profile's tweets once before, \
    subsequent calls to this command will break off when they encounter an existing tweet. Passing \
    `--ignore_backfill` to this command will override this behavior and force it to iterate the whole timeline.
    :param overwrite: (Optional) By default, Django Twitter will skip over any existing tweets and will not \
    overwrite any of their data. If you pass `--overwrite` this behavior will be overridden, and if the command \
    encounters existing tweets (e.g. if you have also passed `--ignore_backfill`) then it will update them with \
    the latest API data.
    :param max_backfill_date: (Optional) A YYYY-MM-DD or MM-DD-YYYY string representing a date at which the \
    `ignore_backfill` behavior should stop. Useful if you want to iterate over and refresh previously-collected \
    tweets (i.e. by also passing `--ignore_backfill` and `--overwrite`) and refresh their stats, but only for \
    recent tweets that were created after a certain date.
    :param max_backfill_days: (Optional) Alternative to `max_backfill_date`; overrides the `--ignore_backfill` \
    behavior but only for tweets that were created within the last N days.
    :param no_progress_bar: (Optional) Disables the default `tqdm` progress bar.
    :param limit: (Optional) Set a limit for the number of tweets to collect for each profile, for testing purposes.

    :param api_key: (Optional) Twitter API key, if you don't have the TWITTER_API_KEY environment variable set
    :param api_secret: (Optional) Twitter API secret, if you don't have the TWITTER_API_SECRET environment variable set
    :param access_token: (Optional) Twitter access token, if you don't have the TWITTER_API_ACCESS_TOKEN environment \
    variable set
    :param api_secret: (Optional) Twitter API access secret, if you don't have the TWITTER_API_ACCESS_SECRET \
    environment variable set

    :param num_cores: Number of cores to use in multiprocessing. Defaults to `multiprocessing.cpu_count()`.
    :param collect_all_once: (Optional) If True, this command will attempt to ensure tweets \
    have been collected for each profile in the set. On subsequent runs, it will pick up where it left off and will \
    only fetch tweets for profiles that do not have any already.
    """

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
        parser.add_argument("--collect_all_once", action="store_true", default=False)

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
        if options["collect_all_once"]:
            twitter_ids = (
                profile_set.profiles.annotate(c=Count("tweets"))
                .filter(c=0)
                .values_list("twitter_id", flat=True)
            )
        else:
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
