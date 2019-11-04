import datetime
import itertools
import pandas as pd

from collections import Counter

from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm

from django.conf import settings
from django.apps import apps
from django.db.models.functions import TruncMonth
from django.db.models import Count

from pewanalytics.text import TextDataFrame


def get_tweet_set(tweet_set_name):

    tweet_set_model = apps.get_model(
        app_label=settings.TWITTER_APP, model_name=settings.TWEET_SET_MODEL
    )
    tweet_set, created = tweet_set_model.objects.get_or_create(name=tweet_set_name)
    return tweet_set


def get_twitter_profile_set(twitter_profile_set_name):

    """
    Helper function to get or create a TwitterProfileSet

    :param twitter_profile_set_name: The name of the profile set
    :return: A TwitterProfileSet object
    """

    twitter_profile_set_model = apps.get_model(
        app_label=settings.TWITTER_APP, model_name=settings.TWITTER_PROFILE_SET_MODEL
    )
    twitter_profile_set, created = twitter_profile_set_model.objects.get_or_create(
        name=twitter_profile_set_name
    )
    return twitter_profile_set


def get_twitter_profile(twitter_id, create=False):

    """
    Helper function to get an existing profile from a Twitter ID. If multiple profiles are returned (Django Twitter
    does not enforce a unique constraint) then the most recently updated profile is selected.

    :param twitter_id: A Twitter ID (NOT a username)
    :param create: If a profile doesn't exist, create it
    :return: An existing TwitterProfile record, if one exists
    """

    profile_model = apps.get_model(
        app_label=settings.TWITTER_APP, model_name=settings.TWITTER_PROFILE_MODEL
    )
    try:
        if create:
            existing_profile, created = profile_model.objects.get_or_create(
                twitter_id=twitter_id
            )
        else:
            existing_profile = profile_model.objects.get(twitter_id=twitter_id)
    except profile_model.DoesNotExist:
        existing_profile = None
    except profile_model.MultipleObjectsReturned:
        print("Warning: multiple profiles found for {}".format(twitter_id))
        print(
            "For flexibility, Django Twitter does not enforce a unique constraint on twitter_id"
        )
        print(
            "But in this case it can't tell which profile to use, so it's picking the most recently updated one"
        )
        existing_profile = profile_model.objects.filter(twitter_id=twitter_id).order_by(
            "-last_update_time"
        )[0]
    return existing_profile


def get_twitter_profile_json(twitter_id, twitter_handler):

    """
    Helper function to get a profile JSON from a Twitter ID. Grabs the JSON from the API, but if an error is returned
    it searches for the profile in the database and updates it with the error code.

    :param twitter_id: A Twitter ID or username
    :param twitter_handler: a TwitterAPIHandler instance
    :return: JSON for the profile
    """

    profile_model = apps.get_model(
        app_label=settings.TWITTER_APP, model_name=settings.TWITTER_PROFILE_MODEL
    )
    twitter_json = twitter_handler.get_profile(twitter_id, return_errors=True)
    if isinstance(twitter_json, int):
        error_code = twitter_json
        existing_profile = get_twitter_profile(twitter_id)
        if existing_profile:
            existing_profile.twitter_error_code = error_code
            existing_profile.save()
        return None
    else:
        return twitter_json


def _identify_unusual_text(profiles, text_col):

    empty = profiles[(profiles[text_col].isnull()) | (profiles[text_col] == "")]
    not_empty = profiles[~(profiles[text_col].isnull()) & ~(profiles[text_col] == "")]
    tdf = TextDataFrame(
        not_empty, text_col, min_df=1, analyzer="char", ngram_range=(1, 10)
    )
    similarities = cosine_similarity(tdf.tfidf, tdf.tfidf)
    not_empty["avg_cosine"] = pd.DataFrame(similarities, index=not_empty.index).mean()
    upper = not_empty["avg_cosine"].mean() + not_empty["avg_cosine"].std() * 2
    most_similar = not_empty[not_empty["avg_cosine"] >= upper].sort_values(
        "avg_cosine", ascending=False
    )
    lower = not_empty["avg_cosine"].mean() - not_empty["avg_cosine"].std() * 2
    most_unique = not_empty[not_empty["avg_cosine"] <= lower].sort_values(
        "avg_cosine", ascending=True
    )
    return (most_similar, most_unique)


def identify_unusual_profiles_by_tweet_text(profiles, most_recent_n=10):

    """
    Auditing function for identifying unusual profiles. Computes cosine similarities between a set of profiles
    based on their most recent `most_recent_n` number of tweets (concatenated together into single documents).
    Returns two DataFrames with profiles whose tweets were two standard deviations above or below the average
    cosine similarity.

    :param profiles: A QuerySet of profiles
    :param most_recent_n: The number of tweets to use for comparing profiles (sorted by most recent)
    :return: A 2-tuple of dataframes (most_similar, most_unique)
    """

    profile_model = apps.get_model(
        app_label=settings.TWITTER_APP, model_name=settings.TWITTER_PROFILE_MODEL
    )
    profiles = pd.DataFrame.from_records(profiles.values("twitter_id"))
    profiles["tweet_text"] = ""
    for twitter_id in tqdm(profiles["twitter_id"].values, desc="Gathering tweet text"):
        if twitter_id:
            tweets = (
                profile_model.objects.get(twitter_id=twitter_id)
                .tweets.filter(text__isnull=False)
                .order_by("-created_at")[:most_recent_n]
            )
            tweets = " ".join([t.text for t in tweets])
            profiles.loc[profiles["twitter_id"] == twitter_id, "tweet_text"] = tweets
    return _identify_unusual_text(profiles, "tweet_text")


def identify_unusual_profiles_by_descriptions(profiles):

    """
    Auditing function for identifying unusual profiles. Computes cosine similarities between a set of profiles
    based on their descriptions. Returns two DataFrames with profiles whose descriptions were two standard
    deviations above or below the average cosine similarity.

    :param profiles: A QuerySet of profiles
    :return: A 2-tuple of dataframes (most_similar, most_unique)
    """

    descriptions = pd.DataFrame.from_records(
        profiles.values("twitter_id", "description")
    )
    return _identify_unusual_text(descriptions, "description")


def get_monthly_twitter_activity(profiles, min_date, max_date=None):

    """
    Auditing function to produce a DataFrame of profiles, showing the number of tweets each profile produced in
    each month in a given range. Useful for identifying whether or not accounts have been fully backfilled, etc.
    Best served with a side of conditional formatting in Excel. Will automatically account for profiles' creation
    dates.

    :param profiles: A QuerySet of profiles
    :param min_date: The starting date
    :param max_date: (Optional) The ending date (defaults to today)
    :return: DataFrame
    """

    tweet_model = apps.get_model(
        app_label=settings.TWITTER_APP, model_name=settings.TWEET_MODEL
    )
    profiles = pd.DataFrame.from_records(
        profiles.values("pk", "name", "screen_name", "created_at")
    )
    tweets = tweet_model.objects.filter(profile_id__in=profiles["pk"].values).filter(
        created_at__gte=min_date
    )
    if max_date:
        tweets = tweets.filter(created_at__lte=max_date)
    tweets = (
        tweets.annotate(month=TruncMonth("created_at"))
        .values("month", "profile_id")
        .annotate(c=Count("pk"))
        .values("profile_id", "month", "c")
    )
    tweets = pd.DataFrame.from_records(tweets)

    all_combos = pd.DataFrame(
        [
            {"profile_id": a, "month": b}
            for a, b in itertools.product(
                profiles["pk"].unique(), tweets["month"].unique()
            )
        ]
    )
    tweets = all_combos.merge(tweets, how="left", on=["profile_id", "month"])

    for index, row in profiles.iterrows():
        tweets.loc[
            (tweets["profile_id"] == row["pk"]) & (tweets["month"] < row["created_at"]),
            "c",
        ] = None
        tweets.loc[
            (tweets["profile_id"] == row["pk"])
            & (tweets["month"] >= row["created_at"])
            & (tweets["c"].isnull()),
            "c",
        ] = 0

    tweets = tweets.pivot(index="profile_id", columns="month", values="c")
    tweets.columns = tweets.columns.map(lambda x: "{}_{}".format(x.year, x.month))
    tweets = tweets.merge(profiles, how="left", left_index=True, right_on="pk")

    return tweets


def find_missing_date_ranges(
    profiles, min_date, max_date=None, min_consecutive_missing_dates=7
):

    """
    Iterates over a set of profiles and finds all periods within a range of dates in which the profile did not
    produce any tweets. Uses `min_consecutive_missing_dates` to specify the minimum number of days a profile
    must be inactive to be worth including. By default, the function will return all 7+ day periods in which
    a profile in the set did not produce any tweets. Will automatically account for profiles' creation dates.

    :param profiles: A QuerySet of profiles
    :param min_date: The starting date
    :param max_date: The ending date (defauts to today)
    :param min_consecutive_missing_dates: Minimum number of consecutive days a profile must be inactive to include
    :return: A DataFrame of date ranges and profile IDs
    """

    rows = []

    try:
        min_date = min_date.date()
    except AttributeError:
        pass
    if not max_date:
        max_date = datetime.datetime.now().date()
    _min_date = min_date
    for profile in tqdm(profiles, desc="Scanning profiles for missing dates"):

        if profile.created_at:
            min_date = max([_min_date, profile.created_at.date()])
        else:
            min_date = _min_date

        existing_dates = [
            d.date()
            for d in profile.tweets.filter(created_at__isnull=False).values_list(
                "created_at", flat=True
            )
        ]
        date_counts = Counter(existing_dates)

        date = min_date
        while date < max_date:

            consecutive = 0
            start_date = date
            while consecutive < min_consecutive_missing_dates and start_date < max_date:

                while date_counts[start_date] > 0:
                    start_date = start_date + datetime.timedelta(days=1)

                end_date = start_date + datetime.timedelta(days=1)
                consecutive = 1
                while date_counts[end_date] == 0:
                    end_date = end_date + datetime.timedelta(days=1)
                    consecutive += 1
                    if end_date >= max_date:
                        break

                if consecutive >= min_consecutive_missing_dates:
                    rows.append(
                        {
                            "twitter_id": profile.twitter_id,
                            "start_date": start_date,
                            "end_date": end_date,
                        }
                    )
                    break
                else:
                    start_date = end_date
            if start_date >= max_date:
                break
            date = end_date

    missing_dates = pd.DataFrame(rows)
    if len(missing_dates) > 0:
        missing_dates["range"] = missing_dates.apply(
            lambda x: (x["end_date"] - x["start_date"]).days, axis=1
        )
        missing_dates = missing_dates.sort_values("range", ascending=False)

    return missing_dates
