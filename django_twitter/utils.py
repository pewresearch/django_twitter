import datetime
import pytz
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


def get_concrete_model(abstract_model_name):

    for model in apps.get_app_config(settings.TWITTER_APP).get_models():
        for base in model.__bases__:
            if base.__name__ == abstract_model_name:
                return model
    return None


def get_tweet_set(tweet_set_name):

    TweetSet = get_concrete_model("AbstractTweetSet")
    tweet_set, created = TweetSet.objects.get_or_create(name=tweet_set_name)
    return tweet_set


def get_twitter_profile_set(twitter_profile_set_name):

    """
    Helper function to get or create a TwitterProfileSet

    :param twitter_profile_set_name: The name of the profile set
    :return: A TwitterProfileSet object
    """

    TwitterProfileSet = get_concrete_model("AbstractTwitterProfileSet")
    twitter_profile_set, created = TwitterProfileSet.objects.get_or_create(
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

    TwitterProfile = get_concrete_model("AbstractTwitterProfile")
    try:
        if create:
            existing_profile, created = TwitterProfile.objects.get_or_create(
                twitter_id=twitter_id
            )
        else:
            existing_profile = TwitterProfile.objects.get(twitter_id=twitter_id)
    except TwitterProfile.DoesNotExist:
        existing_profile = None
    except TwitterProfile.MultipleObjectsReturned:
        print("Warning: multiple profiles found for {}".format(twitter_id))
        print(
            "For flexibility, Django Twitter does not enforce a unique constraint on twitter_id"
        )
        print(
            "But in this case it can't tell which profile to use, so it's picking the most recently updated one"
        )
        existing_profile = TwitterProfile.objects.filter(
            twitter_id=twitter_id
        ).order_by("-last_update_time")[0]
    return existing_profile


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

    TwitterProfile = get_concrete_model("AbstractTwitterProfile")
    profiles = pd.DataFrame.from_records(profiles.values("twitter_id"))
    profiles["tweet_text"] = ""
    for twitter_id in tqdm(profiles["twitter_id"].values, desc="Gathering tweet text"):
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
        lambda x: TwitterProfile.objects.get(pk=x).most_recent_snapshot().name
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


def get_twitter_profile_dataframe(profiles, date, *extra_values):
    """
    Given a QuerySet of TwitterProfile objects and a date, returns a dataframe of the profiles. The date is used to
    scan each profile's historical records and find the snapshot closest to the date requested, without exceeding the
    date.  For example, if you pass in `datetime(2019, 12, 31)`, and a profile has history for 11/1/19 and 1/1/20, the
    former will be returned. The exact date of the snapshot is provided in the `history_date` column.

    :param profiles: A QuerySet of TwitterProfile objects
    :param date: The function will attempt to return profiles as they appeared as of the date provided
    :param extra_values: Additional arguments can be used to select additional fields to return (operates the same as
    requesting fields via `TwitterProfile.objects.values(field1, field2)`
    :return: A DataFrame representing the TwitterProfiles at a certain point in time
    """

    rows = []
    for profile in profiles:

        lt_history = profile.history.filter(history_date__lte=date).order_by(
            "-history_date"
        )
        gt_history = profile.history.filter(history_date__gte=date).order_by(
            "history_date"
        )

        if isinstance(date, datetime.date):
            date = datetime.datetime(
                date.year, date.month, date.day, tzinfo=pytz.timezone("US/Eastern")
            )

        if lt_history.count() > 0 and gt_history.count() > 0:
            lt_diff = date - (lt_history[0].history_date)
            gt_diff = (gt_history[0].history_date) - date
            if gt_diff > lt_diff:
                history = gt_history
            else:
                history = lt_history
        elif lt_history.count() > 0:
            history = lt_history
        elif gt_history.count() > 0:
            history = gt_history
        else:
            history = None

        if history:
            row = history.values(
                "twitter_id",
                "last_update_time",
                "historical",
                "name",
                "screen_name",
                "description",
                "status",
                "is_verified",
                "is_private",
                "created_at",
                "location",
                "language",
                "twitter_error_code",
                "history_date",
                *extra_values
            )[0]
            row["most_recent_history"] = profile.history.order_by("-history_date")[
                0
            ].history_date
            row["earliest_history"] = profile.history.order_by("history_date")[
                0
            ].history_date
            rows.append(row)
    df = pd.DataFrame(rows)
    if len(rows) > 0:
        df["created_at"] = df["created_at"].dt.tz_convert(tz="US/Eastern")
        df["last_update_time"] = df["last_update_time"].dt.tz_convert(tz="US/Eastern")
        df["history_date"] = df["history_date"].dt.tz_convert(tz="US/Eastern")
        df["most_recent_history"] = df["most_recent_history"].dt.tz_convert(
            tz="US/Eastern"
        )
        df["earliest_history"] = df["earliest_history"].dt.tz_convert(tz="US/Eastern")

    return df


def get_tweet_dataframe(profiles, start_date, end_date, *extra_values, **kwargs):

    """
    Given a QuerySet of TwitterProfile objects, returns all of the tweets produced by the profiles within a certain
    date range.

    :param profiles: A QuerySet of TwitterProfile objects
    :param start_date: Returns tweets created on or after this date
    :param end_date: Returns tweets created on or before this date
    :param extra_values: Additional arguments can be used to select additional fields to return (operates the same as
    requesting fields via `Tweet.objects.values(field1, field2)`
    :include_profile_stats: Whether or not to interpolate profile statistics like follower counts over time based on available snapshots (default is False)
    :return:
    """

    Tweet = get_concrete_model("AbstractTweet")
    tweets = (
        Tweet.objects.filter(profile__in=profiles)
        .filter(created_at__lte=end_date)
        .filter(created_at__gte=start_date)
        .values(
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
    df["created_at"] = pd.to_datetime(df["created_at"]).dt.tz_convert(tz="US/Eastern")
    df["last_update_time"] = pd.to_datetime(df["last_update_time"]).dt.tz_convert(
        tz="US/Eastern"
    )
    df["date"] = (
        pd.to_datetime(df["created_at"])
        .dt.tz_convert(tz="US/Eastern")
        .map(lambda x: x.date())
    )

    if "include_profile_stats" in kwargs.keys() and kwargs["include_profile_stats"]:
        all_stats = []
        for twitter_id in df["profile"].unique():
            profile = get_concrete_model("AbstractTwitterProfile").objects.get(
                twitter_id=twitter_id
            )
            stats = pd.DataFrame.from_records(
                profile.history.values(
                    "history_date",
                    "followers_count",
                    "favorites_count",
                    "followings_count",
                    "listed_count",
                    "statuses_count",
                )
            )
            # Since history objects get created any time ANYTHING changes on a model, they don't necessarily represent handshakes with the API
            # So by de-duping like so:
            stats = stats.sort_values("history_date").drop_duplicates(
                subset=[
                    "followers_count",
                    "favorites_count",
                    "followings_count",
                    "listed_count",
                    "statuses_count",
                ]
            )
            # We can isolate those handshakes by filtering down to timestamps when the stats values changed
            # Which could only have occurred via an API update
            stats = stats.set_index("history_date").resample("D").max()
            stats["followers_count"] = stats["followers_count"].interpolate(
                limit_area="inside"
            )
            stats["favorites_count"] = stats["favorites_count"].interpolate(
                limit_area="inside"
            )
            stats["followings_count"] = stats["followings_count"].interpolate(
                limit_area="inside"
            )
            stats["listed_count"] = stats["listed_count"].interpolate(
                limit_area="inside"
            )
            stats["statuses_count"] = stats["statuses_count"].interpolate(
                limit_area="inside"
            )
            stats["profile"] = twitter_id
            stats = stats.reset_index().rename(columns={"history_date": "date"})
            stats["date"] = stats["date"].map(lambda x: x.date())
            all_stats.append(stats)
        all_stats = pd.concat(all_stats)
        all_stats.columns = [
            "profile_{}".format(c) if c not in ["profile", "date"] else c
            for c in all_stats.columns
        ]
        df = df.merge(all_stats, how="left", on=("profile", "date"))

    return df
