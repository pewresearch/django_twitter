from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
from builtins import object

import re
import json
import simple_history
import django
import itertools
import copy
import pytz
import datetime
import pandas as pd
import traceback

from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone
from django.conf import settings
from django.apps import apps

from picklefield.fields import PickledObjectField
from simple_history import register
from simple_history.models import HistoricalRecords
from dateutil.parser import parse as date_parse
from difflib import SequenceMatcher
from collections import defaultdict

from pewtils import decode_text, is_not_null, is_null
from django_pewtils import consolidate_objects
from future.utils import with_metaclass

from django_twitter.utils import get_concrete_model, safe_get_or_create


class AbstractTwitterBase(models.base.ModelBase):

    """
    All django_twitter models inherit from this base class. When a model in your own app, in turn, inherits from a
    django_twitter model (like AbstractTweet), the code below will intercept the model when it's initialized, and
    then look other django_twitter-based models in your own app that should have relationships between each other.
    django_twitter doesn't know anything about your app but if you configure your settings.py model correctly,
    it will be able to connect all your models together at runtime.
    """

    class Meta(object):
        abstract = True

    def __new__(cls, name, bases, attrs):
        """
        Overrides Django's __new__ function and uses it to auto-detect the models in your own app that implement \
        Django Twitter's abstract models, and auto-creates relations between them at runtime.
        """

        model = super(AbstractTwitterBase, cls).__new__(cls, name, bases, attrs)
        for base in bases:
            model_name = re.sub("Abstract", "", base.__name__) + "Model"
            if base.__module__.startswith("django_twitter"):
                setattr(cls, model_name, model)

        counts = defaultdict(int)
        fields_to_add = {
            "TweetModel": [
                (
                    models.ForeignKey,
                    "TwitterProfileModel",
                    "profile",
                    "tweets",
                    None,
                    True,
                    models.CASCADE,
                ),
                (
                    models.ManyToManyField,
                    "TwitterHashtagModel",
                    "hashtags",
                    "tweets",
                    None,
                    True,
                    None,
                ),
                (
                    models.ManyToManyField,
                    "TwitterProfileModel",
                    "profile_mentions",
                    "tweet_mentions",
                    None,
                    True,
                    None,
                ),
                (
                    models.ForeignKey,
                    "TweetModel",
                    "retweeted_status",
                    "retweets",
                    None,
                    True,
                    models.SET_NULL,
                ),
                (
                    models.ForeignKey,
                    "TweetModel",
                    "in_reply_to_status",
                    "replies",
                    None,
                    True,
                    models.SET_NULL,
                ),
                (
                    models.ForeignKey,
                    "TweetModel",
                    "quoted_status",
                    "quotes",
                    None,
                    True,
                    models.SET_NULL,
                ),
            ],
            "TwitterFollowerListModel": [
                (
                    models.ForeignKey,
                    "TwitterProfileModel",
                    "profile",
                    "follower_lists",
                    None,
                    True,
                    models.CASCADE,
                ),
                (
                    models.ManyToManyField,
                    "TwitterProfileModel",
                    "followers",
                    None,
                    None,
                    True,
                    None,
                ),
            ],
            "TwitterFollowingListModel": [
                (
                    models.ForeignKey,
                    "TwitterProfileModel",
                    "profile",
                    "following_lists",
                    None,
                    True,
                    models.CASCADE,
                ),
                (
                    models.ManyToManyField,
                    "TwitterProfileModel",
                    "followings",
                    None,
                    None,
                    True,
                    None,
                ),
            ],
            "TwitterProfileSnapshotModel": [
                (
                    models.ForeignKey,
                    "TwitterProfileModel",
                    "profile",
                    "snapshots",
                    None,
                    True,
                    models.CASCADE,
                )
            ],
            "TwitterProfileModel": [
                (
                    models.ForeignKey,
                    "TwitterProfileSnapshotModel",
                    "most_recent_snapshot",
                    "+",
                    None,
                    True,
                    models.SET_NULL,
                )
            ],
            "TweetSetModel": [
                (
                    models.ManyToManyField,
                    "TweetModel",
                    "tweets",
                    "tweet_sets",
                    None,
                    True,
                    None,
                )
            ],
            "TwitterProfileSetModel": [
                (
                    models.ManyToManyField,
                    "TwitterProfileModel",
                    "profiles",
                    "twitter_profile_sets",
                    None,
                    True,
                    None,
                )
            ],
        }
        throughs = []
        for owner_model in list(fields_to_add.keys()):
            for (
                relationship_type,
                related_model,
                field_name,
                related_name,
                through,
                symmetrical,
                on_delete,
            ) in fields_to_add[owner_model]:

                if (
                    hasattr(cls, owner_model)
                    and hasattr(cls, related_model)
                    and getattr(cls, owner_model)
                    and getattr(cls, related_model)
                    and (
                        not through or (hasattr(cls, through) and getattr(cls, through))
                    )
                ):
                    try:
                        getattr(cls, owner_model)._meta.get_field(field_name)
                    except django.core.exceptions.FieldDoesNotExist:
                        field_params = {"related_name": related_name}
                        if through:
                            field_params["through"] = getattr(cls, through)
                        if not symmetrical:
                            field_params["symmetrical"] = symmetrical
                        if (
                            relationship_type != models.ManyToManyField
                            and owner_model not in throughs
                        ):
                            field_params["null"] = True
                        if is_not_null(on_delete):
                            getattr(cls, owner_model).add_to_class(
                                field_name,
                                relationship_type(
                                    getattr(cls, related_model),
                                    on_delete,
                                    **field_params
                                ),
                            )
                        else:
                            getattr(cls, owner_model).add_to_class(
                                field_name,
                                relationship_type(
                                    getattr(cls, related_model), **field_params
                                ),
                            )
                    counts[owner_model] += 1
                    if counts[owner_model] == len(fields_to_add[owner_model]):
                        for base1 in getattr(cls, owner_model).__bases__:
                            for base2 in base1.__bases__:
                                if base2.__name__ == "AbstractTwitterObject":
                                    try:
                                        history = HistoricalRecords()
                                        history.contribute_to_class(
                                            getattr(cls, owner_model), "history"
                                        )
                                        register(getattr(cls, owner_model))
                                    except simple_history.exceptions.MultipleRegistrationsError:
                                        pass

        return model


class AbstractTwitterObject(models.Model):
    """
    A base class for all Twitter models, including a unique Twitter ID and a
    timestamp reflecting when the object was last updated. Also has a `historical` boolean field \
    that you can use for your own purposes (e.g. for flagging and skipping outdated accounts during \
    data collection, etc.)
    """

    class Meta(object):
        abstract = True

    twitter_id = models.CharField(
        max_length=150,
        db_index=True,
        unique=True,
        help_text="The object's unique Twitter ID",
    )
    last_update_time = models.DateTimeField(
        auto_now=True, help_text="Last time the object was updated"
    )
    historical = models.BooleanField(
        default=False,
        help_text="Empty flag that you can use to track historical accounts",
    )

    def save(self, *args, **kwargs):
        """
        Strings and lowercases Twitter IDs and updates `last_update_time` every time the object is saved.
        """
        self.twitter_id = str(self.twitter_id).lower()
        self.last_update_time = timezone.now()
        super(AbstractTwitterObject, self).save(*args, **kwargs)


class AbstractTwitterProfile(
    with_metaclass(AbstractTwitterBase, AbstractTwitterObject)
):
    """
    Model for storing basic Twitter profile information - it's unique Twitter ID, when it was created, whether its \
    tweets have been backfilled, etc.

    AUTO-CREATED RELATIONSHIPS:
        - most_recent_snapshot = models.ForeignKey(your_app.TwitterProfileSnapshot, related_name="+")
    """

    class Meta(object):
        abstract = True

    tweet_backfilled = models.BooleanField(
        default=False,
        help_text="An indicator used in the `django_twitter_get_profile` command; True indicates that the profile's \
        tweet history has been backfilled as far as possible, so the sync function will stop after it hits an existing \
        tweet the next time it runs, unless you override this behavior.",
    )

    screen_name = models.CharField(
        max_length=100, db_index=True, null=True, help_text="The profile's screen name"
    )
    created_at = models.DateTimeField(
        null=True, help_text="When the profile was created"
    )
    twitter_error_code = models.IntegerField(
        null=True,
        help_text="The latest error code encountered when attempting to collect this profile's data from the API",
    )

    def __str__(self):

        return str(
            "{0}: http://twitter.com/{0}".format(self.screen_name)
            if self.screen_name
            else self.twitter_id
        )

    def save(self, *args, **kwargs):
        """
        Updates the profile's `most_recent_snapshot` relation every time the profile gets saved.
        """

        if self.snapshots.count() > 0:
            self.most_recent_snapshot = self.snapshots.order_by("-timestamp")[0]
        super(AbstractTwitterProfile, self).save(*args, **kwargs)

    def url(self):
        """
        :return: A URL to the profile's Twitter page
        """
        return "http://www.twitter.com/intent/user?user_id={0}".format(
            self.twitter_id
        )  # Can we verify this? Never seen it

    def get_snapshots(self, start_date, end_date, *extra_values, **kwargs):
        """
        Loops over the profile's snapshots for a given time range, and compiles a Pandas DataFrame of the profile's \
        dynamic data (e.g. follower counts, description, etc.) Uses linear interpolation to fill in missing days for \
        numeric values, and front-filling for non-numeric values.

        :param start_date: The start of the date range you want to extract
        :type start_date: `datetime.datetime` or `datetime.date`
        :param end_date: The end of the date range you want to extract
        :type end_date: `datetime.datetime` or `datetime.date`
        :param extra_values: If you would like to include additional fields (e.g. foreign keys from related objects) \
        you can pass their names as related objects (e.g. "profile__politician_id")
        :param skip_interpolation: (Optional) Disables the default interpolation. Will keep days with missing values \
        empty.
        :return: Pandas DataFrame of the profile's snapshots
        """
        skip_interpolation = kwargs.get("skip_interpolation", False)

        start_date = datetime.datetime(
            start_date.year,
            start_date.month,
            start_date.day,
            0,
            0,
            0,
            tzinfo=pytz.timezone("US/Eastern"),
        )
        end_date = datetime.datetime(
            end_date.year,
            end_date.month,
            end_date.day,
            23,
            59,
            59,
            tzinfo=pytz.timezone("US/Eastern"),
        )
        columns = [
            "description",
            "timestamp",
            "followers_count",
            "favorites_count",
            "followings_count",
            "listed_count",
            "statuses_count",
            "name",
            "screen_name",
            "status",
            "is_verified",
            "is_protected",
            "location",
            "profile__created_at",
            "profile__twitter_error_code",
        ]
        columns.extend(extra_values)
        stats = pd.DataFrame.from_records(self.snapshots.values(*columns)).rename(
            columns={
                "profile__created_at": "created_at",
                "profile__twitter_error_code": "twitter_error_code",
            }
        )
        if len(stats) == 0:
            stats = pd.DataFrame(columns=columns).rename(
                columns={
                    "profile__created_at": "created_at",
                    "profile__twitter_error_code": "twitter_error_code",
                }
            )

        try:
            stats["timestamp"] = pd.to_datetime(stats["timestamp"]).dt.tz_convert(
                tz="US/Eastern"
            )
        except TypeError:
            try:
                stats["timestamp"] = pd.to_datetime(stats["timestamp"]).dt.tz_localize(
                    tz="US/Eastern"
                )
            except:
                stats["timestamp"] = pd.to_datetime(stats["timestamp"]).dt.tz_localize(
                    tz="US/Eastern", ambiguous=True
                )

        if stats["timestamp"].min() > start_date:
            stats = pd.concat([stats, pd.DataFrame([{"timestamp": start_date}])])
        else:
            min_date = stats[stats["timestamp"] <= start_date]["timestamp"].max()
            stats = stats[stats["timestamp"] >= min_date]
        if stats["timestamp"].max() < end_date:
            stats = pd.concat([stats, pd.DataFrame([{"timestamp": end_date}])])
        else:
            max_date = stats[stats["timestamp"] >= end_date]["timestamp"].min()
            stats = stats[stats["timestamp"] <= max_date]

        stats = (
            stats.sort_values("timestamp", ascending=False)
            .set_index("timestamp")
            .resample("D")
            .first()
        )
        # Resampling drops null columns so we're adding them back in
        for col in columns:
            if (
                col
                not in [
                    "timestamp",
                    "profile__created_at",
                    "profile__twitter_error_code",
                ]
                and col not in stats.columns
            ):
                stats[col] = None

        if not skip_interpolation:
            for col in [
                "followers_count",
                "favorites_count",
                "followings_count",
                "listed_count",
                "statuses_count",
            ]:
                stats[col] = stats[col].interpolate(
                    limit_area="inside", limit_direction="forward", method="linear"
                )
            for col in [
                "description",
                "name",
                "screen_name",
                "status",
                "is_verified",
                "is_protected",
                "created_at",
                "location",
                "twitter_error_code",
            ]:
                stats[col] = stats[col].interpolate(
                    limit_area="inside", limit_direction="forward", method="pad"
                )
            for col in extra_values:
                stats[col] = stats[col].interpolate(
                    limit_area="inside", limit_direction="forward", method="pad"
                )
        stats = stats.reset_index().rename(columns={"timestamp": "date"})
        stats["date"] = stats["date"].map(lambda x: x.date())
        stats = stats[
            (stats["date"] >= start_date.date()) & (stats["date"] <= end_date.date())
        ]

        stats["twitter_id"] = self.twitter_id
        stats["pk"] = self.pk
        stats[["description", "name", "screen_name", "status", "location"]] = (
            stats[["description", "name", "screen_name", "status", "location"]]
            .fillna("")
            .apply(lambda x: x.str.replace("\r", " "))
        )

        return stats

    # TODO: these should be renamed "most_recent_followers" etc. because that's more accurate
    def current_followers(self):
        """
        Helper function to return a QuerySet of follower profiles from the profile's most recently collected \
        follower list.
        :return: QuerySet of TwitterProfiles for followers
        """

        try:
            followers = self.follower_lists.filter(finish_time__isnull=False).order_by(
                "-finish_time"
            )[0]
        except IndexError:
            followers = None
        return followers.followers.all()

    def current_follower_list(self):
        """
        Helper function to return the profile's most recently collected follower list
        :return: TwitterFollowerList
        """

        try:
            followers = self.follower_lists.filter(finish_time__isnull=False).order_by(
                "-finish_time"
            )[0]
        except IndexError:
            followers = None
        return followers

    def current_followings(self):
        """
        Helper function to return a QuerySet of following profiles from the profile's most recently collected \
        following list.
        :return: QuerySet of TwitterProfiles for followings
        """
        try:
            followings = self.following_lists.filter(
                finish_time__isnull=False
            ).order_by("-finish_time")[0]
        except IndexError:
            followings = None
        return followings.followings.all()

    def current_following_list(self):
        """
        Helper function to return the profile's most recently collected following list
        :return: TwitterFollowingList
        """
        try:
            followings = self.following_lists.filter(
                finish_time__isnull=False
            ).order_by("-finish_time")[0]
        except IndexError:
            followings = None
        return followings


class AbstractTwitterProfileSnapshot(with_metaclass(AbstractTwitterBase, models.Model)):
    """
    Stores a representation of a Twitter profile as it existed in the API at the time of data collection.

    AUTO-CREATED RELATIONSHIPS:
        - profile = models.ForeignKey(your_app.TwitterProfileModel, related_name="snapshots")
    """

    class Meta(object):
        abstract = True

    timestamp = models.DateTimeField(
        auto_now_add=True, help_text="Timestamp indicating when the snapshot was saved"
    )

    screen_name = models.CharField(
        max_length=100, db_index=True, null=True, help_text="The profile's screen name"
    )
    name = models.CharField(
        max_length=200, null=True, help_text="The name of the profile"
    )
    contributors_enabled = models.BooleanField(
        null=True, help_text="Whether or not the profile allows contributors"
    )
    description = models.TextField(null=True, help_text="The profile's description/bio")
    favorites_count = models.IntegerField(
        null=True, help_text="Number of favorited tweets"
    )
    followers_count = models.IntegerField(null=True, help_text="Number of followers")
    followings_count = models.IntegerField(
        null=True, help_text="Number of accounts the profile follows ('followings')"
    )
    is_verified = models.BooleanField(
        null=True, help_text="Whether or not the profile is verified"
    )
    is_protected = models.BooleanField(
        null=True, help_text="Whether or not the profile is protected"
    )
    listed_count = models.IntegerField(null=True, help_text="")
    profile_image_url = models.TextField(
        null=True, help_text="URL to the profile's picture"
    )
    status = models.TextField(null=True, help_text="The profile's current status")
    statuses_count = models.IntegerField(
        null=True, help_text="Number of tweets the profile has produced"
    )
    urls = ArrayField(
        models.CharField(max_length=300),
        default=list,
        help_text="A list of URLs contained in the profile's bio",
    )
    location = models.CharField(
        max_length=512, null=True, help_text="The profile's self-reported location"
    )
    json = models.JSONField(
        null=True,
        default=dict,
        help_text="The raw JSON for the profile at the time the snapshot was collected",
    )

    def __str__(self):

        return "{} AS OF {}".format(str(self.profile), self.timestamp)

    # TODO: these should actually try to grab the lists that are closest to the snapshot's timestamp
    # @property
    # def followers(self):
    #     follower_list = self.follower_lists.filter(finish_time__isnull=False).order_by(
    #         "-finish_time"
    #     )[0]
    #     return follower_list.followers.all()
    #
    # @property
    # def followings(self):
    #     following_list = self.following_lists.filter(
    #         finish_time__isnull=False
    #     ).order_by("-finish_time")[0]
    #     return following_list.followings.all()

    def update_from_json(self, profile_data=None):
        """
        Parses raw JSON collected from the Twitter API into the various fields and relations. If no new JSON is passed, \
        the snapshot will update itself using whatever it already has stored in its `json` field.

        :param profile_data: JSON from the API
        """

        if not profile_data:
            profile_data = self.json

        if not hasattr(profile_data, "keys"):
            while not hasattr(profile_data, "keys"):
                profile_data = json.loads(profile_data)

        if profile_data:
            for db_name, api_name in [
                ("name", None),
                ("contributors_enabled", None),
                ("description", None),
                ("followers_count", None),
                ("followings_count", "friends_count"),
                ("is_verified", "verified"),
                ("is_protected", "protected"),
                ("listed_count", None),
                ("location", None),
                ("profile_image_url", None),
                ("statuses_count", None),
            ]:
                if not api_name or len(api_name) < 1:
                    api_name = db_name

                if api_name in profile_data:
                    setattr(self, db_name, profile_data[api_name])

            self.profile.created_at = date_parse(profile_data["created_at"])
            self.profile.screen_name = profile_data["screen_name"].lower()
            self.profile.save()

            self.screen_name = profile_data["screen_name"].lower()
            self.favorites_count = (
                profile_data["favorites_count"]
                if "favorites_count" in list(profile_data.keys())
                else profile_data["favourites_count"]
            )
            self.status = (
                profile_data["status"]["text"]
                if "status" in list(profile_data.keys())
                else None
            )

            if "url" in list(profile_data.get("entities", {}).keys()):
                urls = [
                    url["expanded_url"]
                    for url in profile_data.get("entities", {})
                    .get("url", {})
                    .get("urls", [])
                    if url["expanded_url"]
                ]
            else:
                urls = [profile_data.get("url", "")]
            urls = [u for u in urls if is_not_null(u)]
            self.urls = urls
            self.json = profile_data
            try:
                self.save()
            except (django.db.utils.IntegrityError, ValueError):
                self.description = decode_text(self.description)
                self.screen_name = decode_text(self.screen_name)
                self.status = decode_text(self.status)
                self.save()

    def url(self):
        """
        Returns a URL to the profile's Twitter page
        """
        return "http://www.twitter.com/intent/user?user_id={0}".format(
            self.twitter_id
        )  # Can we verify this? Never seen it


class AbstractTweet(with_metaclass(AbstractTwitterBase, AbstractTwitterObject)):
    """
    A template for storing data contained in a tweet.

    AUTO-CREATED RELATIONSHIPS:
        - profile = models.ForeignKey(your_app.TwitterProfileModel, related_name="tweets")
        - hashtags = models.ManyToManyField(your_app.TwitterHashtagModel, related_name="tweets")
        - profile_mentions = models.ManyToManyField(your_app.TwitterProfileModel, related_name="tweet_mentions")
        - retweeted_status = models.ForeignKey(your_app.TweetModel, related_name="retweets")
        - in_reply_to_status = models.ForeignKey(your_app.TweetModel, related_name="replies")
        - quoted_status = models.ForeignKey(your_app.TweetModel, related_name="quotes")
    """

    class Meta(object):
        abstract = True

    created_at = models.DateTimeField(
        null=True, help_text="The time/date that the tweet was published"
    )
    links = ArrayField(
        models.CharField(max_length=400),
        null=True,
        help_text="Links contained in the tweet",
    )

    media = ArrayField(
        models.JSONField(null=True), null=True, help_text="Media contained in the tweet"
    )

    text = models.CharField(
        max_length=1500,
        null=True,
        help_text="Text extracted from the tweet, including expanded text and text from tweets that it quoted or retweeted (hence why the max length is longer than the twitter size limit",
    )

    profile_mentions_raw = ArrayField(
        models.CharField(max_length=280),
        default=list,
        null=True,
        help_text="A list of profile screen names that were mentioned in the tweet",
    )

    language = models.CharField(
        max_length=255, null=True, help_text="The tweet's language"
    )

    retweet_count = models.IntegerField(
        null=True,
        help_text="Number of times the tweet was retweeted. Note: for tweets that are retweets (but not quote tweets), this count reflects the _original_ tweet's retweets, not just the retweeted version's retweets. When someone retweets a retweet that didn't have any additional commentary, that retweet gets redirected back to the original tweet.",
    )
    favorite_count = models.IntegerField(
        null=True,
        help_text="Number of times the tweet was favorited. Note: for tweets that are retweets (but not quote tweets), this count reflects the _original_ tweet's favorites, not just the retweeted version's favorites. When someone favorites a retweet that didn't have any additional commentary, that favorite gets redirected back to the original tweet.",
    )

    json = models.JSONField(
        null=True, default=dict, help_text="The raw JSON for the tweet"
    )

    def __str__(self):

        return "{0}, {1}:\nhttps://twitter.com/{2}/status/{3}/:\n {4}".format(
            self.profile if self.profile else None,
            self.created_at,
            self.profile.screen_name if self.profile else None,
            self.twitter_id,
            decode_text(self.text),
        )

    def update_from_json(self, tweet_data=None):

        """
        Parses raw JSON collected from the Twitter API into the various fields and relations. If no new JSON is passed, \
        the tweet will update itself using whatever it already has stored in its `json` field.

        :param tweet_data: JSON from the API
        """
        Tweet = get_concrete_model("AbstractTweet")
        TwitterProfile = get_concrete_model("AbstractTwitterProfile")
        TwitterProfileSnapshot = get_concrete_model("AbstractTwitterProfileSnapshot")
        TwitterHashtag = get_concrete_model("AbstractTwitterHashtag")

        def _consolidate_duplicate_tweets(twitter_id):
            tweets = Tweet.objects.filter(twitter_id=twitter_id)
            target = tweets[0]
            for tweet in tweets.exclude(pk=target.pk):
                consolidate_objects(source=tweet, target=target)
            target.refresh_from_db()
            return target

        if not tweet_data:
            tweet_data = self.json
        if tweet_data:

            if not hasattr(tweet_data, "keys"):
                while not hasattr(tweet_data, "keys"):
                    tweet_data = json.loads(tweet_data)

            if not self.pk:
                self.save()
                self.refresh_from_db()

            # PROFILE
            author = safe_get_or_create(
                "AbstractTwitterProfile",
                "twitter_id",
                tweet_data["user"]["id_str"],
                create=True,
            )
            snapshot = TwitterProfileSnapshot.objects.create(
                profile=author, json=tweet_data["user"]
            )
            snapshot.update_from_json()
            self.profile = author

            # PROFILE MENTIONS
            profile_mentions = []
            for profile_mention in tweet_data.get("entities", {}).get(
                "user_mentions", []
            ):
                mentioned_profile = safe_get_or_create(
                    "AbstractTwitterProfile",
                    "twitter_id",
                    profile_mention["id_str"],
                    create=True,
                )
                profile_mentions.append(mentioned_profile)
            self.profile_mentions.set(profile_mentions)

            # HASHTAGS
            hashtags = []
            for hashtag in tweet_data.get("entities", {}).get("hashtags", []):
                hashtag_obj = safe_get_or_create(
                    "AbstractTwitterHashtag",
                    "name",
                    hashtag["text"].lower(),
                    create=True,
                )
                hashtags.append(hashtag_obj)
            self.hashtags.set(hashtags)

            # REPLY TO STATUS
            if tweet_data.get("in_reply_to_status_id", None):
                tweet_obj = safe_get_or_create(
                    "AbstractTweet",
                    "twitter_id",
                    tweet_data["in_reply_to_status_id_str"].lower(),
                    create=True,
                )
                tweet_obj.refresh_from_db()
                if not tweet_obj.profile and tweet_data.get(
                    "in_reply_to_user_id_str", None
                ):
                    reply_author_obj = safe_get_or_create(
                        "AbstractTwitterProfile",
                        "twitter_id",
                        tweet_data["in_reply_to_user_id_str"].lower(),
                        create=True,
                    )
                    tweet_obj.profile = reply_author_obj
                    tweet_obj.save()
                self.in_reply_to_status = tweet_obj

            # QUOTE STATUS
            if tweet_data.get("quoted_status", None):
                tweet_obj = safe_get_or_create(
                    "AbstractTweet",
                    "twitter_id",
                    tweet_data["quoted_status"]["id_str"].lower(),
                    create=True,
                )
                tweet_obj.refresh_from_db()
                tweet_obj.update_from_json(tweet_data["quoted_status"])
                self.quoted_status = tweet_obj

            # RETWEETED STATUS
            if tweet_data.get("retweeted_status", None):
                tweet_obj = safe_get_or_create(
                    "AbstractTweet",
                    "twitter_id",
                    tweet_data["retweeted_status"]["id_str"].lower(),
                    create=True,
                )
                tweet_obj.refresh_from_db()
                tweet_obj.update_from_json(tweet_data["retweeted_status"])
                self.retweeted_status = tweet_obj

            # UPDATE TWEET
            self.created_at = date_parse(tweet_data["created_at"])
            self.retweet_count = tweet_data.get("retweet_count", None)
            self.favorite_count = tweet_data.get("favorite_count", None)
            self.language = tweet_data.get("lang", None)

            # Discovered full_text areas:
            # extended_tweet/full_text/
            # retweeted_status/extended_tweet/full_text/
            # quoted_status/extended_tweet/full_text/
            # retweeted_status/quoted_status/extended_tweet/full_text/

            text_patterns = [[], ["extended_tweet"]]
            additional_text_patterns = [
                ["retweeted_status", "extended_tweet"],
                ["quoted_status", "extended_tweet"],
                ["retweeted_status", "quoted_status"],
                ["retweeted_status", "quoted_status", "extended_tweet"],
                ["retweeted_status"],
                ["quoted_status"],
            ]
            text_keys = ["full_text", "text"]

            def get_text(tweet_data):

                all_text = []

                for keys in text_patterns:
                    subset = tweet_data
                    for key in keys:
                        subset = subset.get(key, {})
                    for text_key in text_keys:
                        if text_key in subset.keys():
                            text = subset[text_key]
                            if text not in all_text:
                                all_text.append(text)

                for keys in additional_text_patterns:
                    subset = tweet_data
                    for key in keys:
                        subset = subset.get(key, {})
                    for text_key in text_keys:
                        if text_key in subset.keys():
                            additional_text = subset[text_key]
                            if additional_text not in all_text:
                                all_text.append(additional_text)

                all_text = [
                    re.sub(text[-1], "", text)
                    if text.endswith("\u2026") or text.endswith("\u2026")
                    else text
                    for text in all_text
                ]
                if len(all_text) > 1:
                    new_all_text = copy.deepcopy(all_text)
                    for text, additional_text in itertools.permutations(all_text, 2):
                        s = SequenceMatcher(None, additional_text, text, autojunk=True)
                        blocks = s.get_matching_blocks()
                        if len(blocks) > 0:
                            new_additional_text = None
                            for block in blocks:
                                if block.size > 1:
                                    overlap = additional_text[
                                        block.a : (block.a + block.size)
                                    ]
                                    if text.endswith(
                                        overlap
                                    ) and additional_text.startswith(overlap):
                                        new_additional_text = additional_text.replace(
                                            overlap, ""
                                        )
                            if new_additional_text is not None:
                                new_all_text = [
                                    t
                                    for t in new_all_text
                                    if t not in [text, additional_text]
                                ]
                                new_all_text.append(
                                    "".join([text, new_additional_text])
                                )
                    all_text = new_all_text

                if len(all_text) > 0:
                    text = " ".join(all_text)
                else:
                    text = None

                return text

            self.text = get_text(tweet_data)
            self.text = "{}".format(self.text)

            ### LINKS

            try:
                links = set(self.links)

            except TypeError:
                links = set()

            for u in tweet_data.get("entities", {}).get("urls", []):
                link = u.get("expanded_url", "")

                if len(link) > 399:
                    link = u.get("url", "")

                if is_not_null(link):
                    links.add(link)

            self.links = list(links)

            ### MEDIA

            media = []
            for m in tweet_data.get("extended_entities", {}).get("media", []):
                try:
                    if m["type"] == "video":
                        element = {
                            "url": None,
                            "bitrate": None,
                            "content_type": None,
                            "duration": None,
                            "aspect_ratio": None,
                        }
                        if "aspect_ratio" in m["video_info"]:
                            element["aspect_ratio"] = ":".join(
                                [str(a) for a in m["video_info"]["aspect_ratio"]]
                            )
                        if "duration_millis" in m["video_info"]:
                            element["duration"] = m["video_info"]["duration_millis"]
                        v = sorted(
                            m["video_info"]["variants"],
                            key=lambda x: x["bitrate"] if "bitrate" in x else 0,
                            reverse=True,
                        )[0]
                        element["url"] = v["url"]
                        element["bitrate"] = v["bitrate"]
                        element["content_type"] = v["content_type"]

                    else:
                        element = {"url": m["media_url_https"]}
                        element["width"] = m["sizes"]["large"]["w"]
                        element["height"] = m["sizes"]["large"]["h"]
                        element["content_type"] = (
                            "image/gif" if m["type"] == "animated_gif" else "image"
                        )

                except:
                    print(traceback.format_exc())
                    element = m

                media.append(element)

            self.media = list(media)

            self.json = tweet_data

            try:
                self.save()

            except:
                try:
                    self.text = decode_text(self.text)
                    self.json = json.loads(decode_text(json.dumps(self.json)))
                    self.save()

                except Exception as e:
                    print(e)

    def url(self):
        """
        Returns a URL for the tweet
        """
        return "http://www.twitter.com/statuses/{0}".format(self.twitter_id)


class AbstractTwitterFollowerList(with_metaclass(AbstractTwitterBase, models.Model)):
    """
    Tracks a specific run of the `django_twitter_get_profile_followers` command. Saves the start and end time of \
    the command, stores all of the observed followers on its `followers` many-to-many relation, and associates itself \
    with the profile it belongs to via `profile`.

    AUTO-GENERATED RELATIONS:
        - profile = models.ForeignKey("TwitterProfile", related_name="follower_lists")
        - followers = models.ManyToManyField("TwitterProfile", related_name=None)

    """

    class Meta(object):
        abstract = True

    start_time = models.DateTimeField(auto_now_add=True)
    finish_time = models.DateTimeField(null=True)


class AbstractTwitterFollowingList(with_metaclass(AbstractTwitterBase, models.Model)):
    """
    Tracks a specific run of the `django_twitter_get_profile_followings` command. Saves the start and end time of \
    the command, stores all of the observed followings on its `followings` many-to-many relation, and associates itself \
    with the profile it belongs to via `profile`.

    AUTO-GENERATED RELATIONS:
        - profile = models.ForeignKey("TwitterProfile", related_name="following_lists")
        - followingss = models.ManyToManyField("TwitterProfile", related_name=None)

    """

    class Meta(object):
        abstract = True

    # profile = models.ForeignKey("TwitterProfile", related_name="following_lists")
    # followings = models.ManyToManyField("TwitterProfile", related_name=None)
    start_time = models.DateTimeField(auto_now_add=True)
    finish_time = models.DateTimeField(null=True)


class AbstractTwitterHashtag(with_metaclass(AbstractTwitterBase, models.Model)):
    """
    Twitter hashtags, represented by a unique string.
    """

    class Meta(object):
        abstract = True

    name = models.CharField(max_length=150, unique=True, db_index=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """
        Lowercases the hashtag before saving
        """
        self.name = self.name.lower()
        super(AbstractTwitterHashtag, self).save(*args, **kwargs)


# def add_historical_records(sender, **kwargs):
#     try: base = sender.__base__.__base__
#     except: base = None
#     if base and base.__module__.startswith("django_twitter") and base.__name__ == "AbstractTwitterObject":
#         history = HistoricalRecords()
#         history.contribute_to_class(sender, "history")
#         register(sender)
#
# class_prepared.connect(add_historical_records)


class AbstractTweetSet(with_metaclass(AbstractTwitterBase, models.Model)):
    """
    A table simply consisting of names associated with particular sets of tweets. You can create these automatically \
    by passing names to the various data collection commands. This allows you to easily reference a set of tweets \
    that was collected by one or more commands.

    AUTO-CREATED RELATIONSHIPS:
        - tweets = models.ManyToManyField(your_app.TweetModel, related_name="tweet_sets")
    """

    class Meta(object):
        abstract = True

    name = models.CharField(
        max_length=256,
        unique=True,
        help_text="A unique name associated with a set of tweets",
    )

    def __str__(self):

        return self.name


class AbstractTwitterProfileSet(with_metaclass(AbstractTwitterBase, models.Model)):
    """
    A table simply consisting of names associated with particular sets of profiles. You can create these automatically \
    by passing names to the various data collection commands. This allows you to easily access and run data collection \
    commands on a set of profiles all at once.

    AUTO-CREATED RELATIONSHIPS:
        - profiles = models.ManyToManyField(your_app.TwitterProfileModel, related_name="twitter_profile_sets")
    """

    class Meta(object):
        abstract = True

    name = models.CharField(
        max_length=256,
        unique=True,
        help_text="A unique name associated with a set of profiles",
    )

    def __str__(self):

        return self.name
