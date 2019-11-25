import pandas as pd

from django.conf import settings
from django.apps import apps


def get_twitter_user(twitter_id, twitter_handler):

    user_model = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWITTER_PROFILE_MODEL)
    twitter_json = twitter_handler.get_user(twitter_id, return_errors=True)
    if isinstance(twitter_json, int):
        error_code = twitter_json
        try:
            existing_profile = user_model.objects.get(twitter_id=twitter_id)
        except user_model.DoesNotExist:
            existing_profile = None
        except user_model.MultipleObjectsReturned:
            print("Warning: multiple users found for {}".format(twitter_id))
            print("For flexibility, Django Twitter does not enforce a unique constraint on twitter_id")
            print("But in this case it can't tell which user to use, so it's picking the most recently updated one")
            existing_profile = user_model.objects.filter(twitter_id=twitter_id).order_by("-last_update_time")[0]
        if existing_profile:
            existing_profile.twitter_error_code = error_code
            existing_profile.save()
        return None
    else:
        return twitter_json


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
        history = profile.history.filter(history_date__lte=date).order_by("-history_date")
        if history.count() > 0:
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
                "favorites_count",
                "followers_count",
                "followings_count",
                "listed_count",
                "statuses_count",
                "twitter_error_code",
                "history_date",
                *extra_values
            )[0]
            row["most_recent_history"] = profile.history.order_by("-history_date")[0].history_date
            row["earliest_history"] = profile.history.order_by("history_date")[0].history_date
            rows.append(row)
    df = pd.DataFrame(rows)
    if len(rows) > 0:
        df['created_at'] = df['created_at'].dt.tz_convert(tz='US/Eastern')
        df['last_update_time'] = df['last_update_time'].dt.tz_convert(tz='US/Eastern')

    return df


def get_tweet_dataframe(profiles, start_date, end_date, *extra_values):

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

    tweet_model = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWEET_MODEL)
    tweets = tweet_model.objects \
        .filter(profile__in=profiles) \
        .filter(created_at__lte=end_date) \
        .filter(created_at__gte=start_date) \
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
    df = pd.DataFrame.from_records(tweets).rename(columns={
        "profile__twitter_id": "profile",
        "retweeted_status__twitter_id": "retweeted_status",
        "in_reply_to_status__twitter_id": "in_reply_to_status",
        "quoted_status__twitter_id": "quoted_status"
    })
    df['created_at'] = df['created_at'].dt.tz_convert(tz='US/Eastern')
    df['last_update_time'] = df['last_update_time'].dt.tz_convert(tz='US/Eastern')

    return df