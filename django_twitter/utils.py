import datetime

import django.db
import pytz
import itertools
import pandas as pd

from collections import Counter
from django.apps import apps
from django.conf import settings
from django.db.models import Count
from django.db.models.functions import TruncMonth
from pewanalytics.text import TextDataFrame
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm
import datetime
import itertools
import os
import pandas as pd
import pytz


def get_concrete_model(abstract_model_name):

    for model in apps.get_app_config(settings.TWITTER_APP).get_models():
        for base in model.__bases__:
            if base.__name__ == abstract_model_name:
                return model
    return None


def safe_get_or_create(model_name, field, value, create=False):
    """
    Helper function to get or create an existing object from an identifier, with error handling for
    mutiprocessing race conditions/collisions.
    """
    kwargs = {field: value}
    Model = get_concrete_model(model_name)  # AbstractTwitterProfile
    try:
        if create:
            try:
                existing, created = Model.objects.get_or_create(**kwargs)
            except django.db.IntegrityError:
                existing = Model.objects.get(**kwargs)
        else:
            existing = Model.objects.get(**kwargs)
    except Model.DoesNotExist:
        existing = None

    return existing


def get_tweet_set(tweet_set_name):

    print("get_tweet_set is deprecated, please use safe_get_or_create")
    return safe_get_or_create("AbstractTweetSet", "name", tweet_set_name, create=True)


def get_twitter_profile_set(twitter_profile_set_name):

    """
    Helper function to get or create a TwitterProfileSet

    :param twitter_profile_set_name: The name of the profile set
    :return: A TwitterProfileSet object
    """

    print("get_twitter_profile_set is deprecated, please use safe_get_or_create")
    return safe_get_or_create(
        "AbstractTwitterProfileSet", "name", twitter_profile_set_name, create=True
    )


def get_twitter_profile(twitter_id, create=False):

    """
    Helper function to get an existing profile from a Twitter ID. If multiple profiles are returned (Django Twitter
    does not enforce a unique constraint) then the most recently updated profile is selected.

    :param twitter_id: A Twitter ID (NOT a username)
    :param create: If a profile doesn't exist, create it
    :return: An existing TwitterProfile record, if one exists
    """

    print("get_twitter_profile is deprecated, please use safe_get_or_create")
    return safe_get_or_create(
        "AbstractTwitterProfile", "twitter_id", twitter_id, create=create
    )


def get_twitter_profile_json(twitter_id, twitter_handler):

    """
    Helper function to get a profile JSON from a Twitter ID. Grabs the JSON from the API, but if an error is returned
    it searches for the profile in the database and updates it with the error code.

    :param twitter_id: A Twitter ID or username
    :param twitter_handler: a TwitterAPIHandler instance
    :return: JSON for the profile
    """

    twitter_json = twitter_handler.get_profile(twitter_id, return_errors=True)
    if isinstance(twitter_json, int):
        error_code = twitter_json
        existing_profile = safe_get_or_create(
            "AbstractTwitterProfile", "twitter_id", twitter_id
        )
        if existing_profile:
            existing_profile.twitter_error_code = error_code
            existing_profile.save()
        return None
    else:
        return twitter_json


def _identify_unusual_text(profiles, text_col):

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

    TwitterProfile = get_concrete_model("AbstractTwitterProfile")
    profiles = pd.DataFrame.from_records(profiles.values("twitter_id"))
    profiles["tweet_text"] = ""
    for twitter_id in tqdm(profiles["twitter_id"].values, desc="Gathering tweet text", disable=os.environ.get("DISABLE_TQDM", False)):
        if twitter_id:
            tweets = (
                TwitterProfile.objects.get(twitter_id=twitter_id)
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
        profiles.values("twitter_id", "snapshots__description", "snapshots__timestamp")
    )
    descriptions = (
        descriptions.sort_values("snapshots__timestamp", ascending=False)
        .groupby("twitter_id")
        .first()
        .reset_index()
    )
    del descriptions["snapshots__timestamp"]
    return _identify_unusual_text(descriptions, "snapshots__description")


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

    Tweet = get_concrete_model("AbstractTweet")
    TwitterProfile = get_concrete_model("AbstractTwitterProfile")
    profiles = pd.DataFrame.from_records(
        profiles.values("pk", "screen_name", "created_at")
    )
    profiles["name"] = profiles["pk"].map(
        lambda x: TwitterProfile.objects.get(pk=x).most_recent_snapshot.name
    )
    tweets = Tweet.objects.filter(profile_id__in=profiles["pk"].values).filter(
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

    idx = pd.date_range(tweets["month"].min(), tweets["month"].max())
    months = tweets[["month"]].drop_duplicates()
    months.index = pd.DatetimeIndex(months["month"])
    months = months.reindex(idx, fill_value="NaN")
    tweets = pd.concat(
        [
            tweets,
            pd.DataFrame(
                [
                    {"month": m}
                    for m in months.index
                    if m.day == 1 and m not in tweets["month"].values
                ]
            ),
        ]
    )
    tweets = tweets.pivot(index="profile_id", columns="month", values="c").fillna(0)
    tweets.columns = tweets.columns.map(lambda x: "{}_{}".format(x.year, x.month))
    tweets = tweets.merge(profiles, how="left", left_index=True, right_on="pk")
    tweets = tweets.dropna(subset=["pk"])

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
    for profile in tqdm(profiles, desc="Scanning profiles for missing dates", disable=os.environ.get("DISABLE_TQDM", False)):

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


def get_twitter_profile_dataframe(
    profiles, start_date, end_date, *extra_values, **kwargs
):
    """
    Given a QuerySet of TwitterProfile objects, a start date, and an end date, returns a dataframe of profile snapshots.
    The resulting dataframe will contain a row for every date and profile, along with profile data as it appeared on
    that date, based on the available snapshots.  Profile statistics, like follower counts, are linearly interpolated
    between snapshots.  Dates for which no snapshot yet existed will have null values.

    :param profiles: A QuerySet of TwitterProfile objects
    :param start_date: The function will attempt to return profiles as they appeared over the timeframe
    :param end_date: The function will attempt to return profiles as they appeared over the timeframe
    :param extra_values: Additional arguments can be used to select additional fields to return (operates the same as
    requesting fields via `TwitterProfile.objects.values(field1, field2)`
    :param skip_interpolation: If you pass `skip_interpolation=True` as a kwarg, values will only be returned for the \
    specific dates that have snapshots. By default, values will be interpolated for missing dates.
    :return: A DataFrame representing the TwitterProfiles at every point in time in the range requested
    """

    stats = []
    for profile in tqdm(profiles, desc="Extracting Twitter profile snapshots", disable=os.environ.get("DISABLE_TQDM", False)):
        stats.append(
            profile.get_snapshots(start_date, end_date, *extra_values, **kwargs)
        )
    return pd.concat(stats)


def get_tweet_dataframe(profiles, start_date, end_date, *extra_values, **kwargs):

    """
    Given a QuerySet of TwitterProfile objects, returns all of the tweets produced by the profiles within a certain
    date range.

    :param profiles: A QuerySet of TwitterProfile objects
    :param start_date: Returns tweets created on or after this date
    :param end_date: Returns tweets created on or before this date
    :param extra_values: Additional arguments can be used to select additional fields to return (operates the same as
    requesting fields via `Tweet.objects.values(field1, field2)`
    :return:
    """

    Tweet = get_concrete_model("AbstractTweet")
    tweets = (
        Tweet.objects.filter(profile__in=profiles)
        .filter(
            created_at__lte=datetime.datetime(
                end_date.year, end_date.month, end_date.day, 23, 59, 59
            )
        )
        .filter(created_at__gte=start_date)
        .values(
            "pk",
            "twitter_id",
            "last_update_time",
            "historical",
            "created_at",
            "text",
            "retweet_count",
            "favorite_count",
            "profile__twitter_id",
            "retweeted_status__twitter_id",
            "in_reply_to_status__twitter_id",
            "quoted_status__twitter_id",
            *extra_values
        )
    )
    df = pd.DataFrame.from_records(tweets).rename(
        columns={
            "profile__twitter_id": "profile",
            "retweeted_status__twitter_id": "retweeted_status",
            "in_reply_to_status__twitter_id": "in_reply_to_status",
            "quoted_status__twitter_id": "quoted_status",
        }
    )
    for date_field in ["created_at", "last_update_time"]:
        try:
            df[date_field] = pd.to_datetime(df[date_field]).dt.tz_convert(
                tz="US/Eastern"
            )
        except TypeError:
            df[date_field] = pd.to_datetime(df[date_field]).dt.tz_localize(
                tz="US/Eastern", ambiguous=True
            )
    df["date"] = df["created_at"].map(lambda x: x.date())
    df["text"] = df["text"].fillna("").apply(lambda x: x.replace("\r", " "))

    df["text"] = df["text"].str.strip()

    # Clear out retweet and favorite counts for retweets since they reflect the original tweet
    df.loc[~df["retweeted_status"].isnull(), "retweet_count"] = None
    df.loc[~df["retweeted_status"].isnull(), "favorite_count"] = None

    return df
