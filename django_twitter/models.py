from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
from builtins import object

import re
import json
import simple_history
import django
import pytz
import datetime
import pandas as pd

from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField
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

from django_twitter.utils import get_twitter_profile, get_concrete_model


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
                    models.ForeignKey,
                    "TwitterPlaceModel",
                    "place",
                    "tweets",
                    None,
                    True,
                    models.SET_NULL,
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
            "BotometerScoreModel": [
                (
                    models.ForeignKey,
                    "TwitterProfileModel",
                    "profile",
                    "botometer_scores",
                    None,
                    True,
                    models.CASCADE,
                )
            ],
            # "TwitterRelationshipModel": [
            #     (
            #         models.ForeignKey,
            #         "TwitterProfileModel",
            #         "following",
            #         "follower_details",
            #         None,
            #         True,
            #         models.CASCADE,
            #     ),
            #     (
            #         models.ForeignKey,
            #         "TwitterProfileModel",
            #         "follower",
            #         "following_details",
            #         None,
            #         True,
            #         models.CASCADE,
            #     ),
            # ],
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
                # (
                #     models.ManyToManyField,
                #     "TwitterProfileModel",
                #     "followers",
                #     "followings",
                #     "TwitterRelationshipModel",
                #     False,
                #     None,
                # )
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
                    except models.fields.FieldDoesNotExist:
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
    class Meta(object):
        abstract = True

    twitter_id = models.CharField(max_length=150, db_index=True)
    last_update_time = models.DateTimeField(auto_now=True)
    historical = models.BooleanField(default=False)
    # TODO: add historical_twitter_ids

    def save(self, *args, **kwargs):
        self.twitter_id = str(self.twitter_id).lower()
        self.last_update_time = timezone.now()
        super(AbstractTwitterObject, self).save(*args, **kwargs)


class AbstractTwitterProfile(
    with_metaclass(AbstractTwitterBase, AbstractTwitterObject)
):
    class Meta(object):
        abstract = True

    tweet_backfilled = models.BooleanField(
        default=False,
        help_text="An indicator used in the sync_tweets management function; True indicates that the profile's \
        tweet history has been backfilled as far as possible, so the sync function will stop after it hits an existing \
        tweet the next time it runs.",
    )

    screen_name = models.CharField(
        max_length=100, db_index=True, null=True, help_text="Twitter screen name"
    )
    created_at = models.DateTimeField(null=True)
    twitter_error_code = models.IntegerField(null=True)

    """
    AUTO-CREATED RELATIONSHIPS:
    followers = models.ManyToManyField(your_app.TwitterProfileModel, related_name="followings")
    most_recent_snapshot = models.ForeignKey(your_app.TwitterProfileSnapshot, related_name="+")
    """

    def __str__(self):

        return str(
            "{0}: http://twitter.com/{0}".format(self.screen_name)
            if self.screen_name
            else self.twitter_id
        )

    def save(self, *args, **kwargs):

        if self.snapshots.count() > 0:
            self.most_recent_snapshot = self.snapshots.order_by("-timestamp")[0]
        super(AbstractTwitterProfile, self).save(*args, **kwargs)

    def url(self):
        return "http://www.twitter.com/intent/user?user_id={0}".format(
            self.twitter_id
        )  # Can we verify this? Never seen it

    def get_snapshots(self, start_date, end_date, *extra_values, **kwargs):

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
            "json",
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
            "is_private",
            "profile__created_at",
            "location",
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
            stats = pd.DataFrame(columns=columns)

        stats["json"] = stats["json"].map(lambda x: str(x))
        stats = stats[stats["json"] != "{}"]
        try:
            stats["timestamp"] = pd.to_datetime(stats["timestamp"]).dt.tz_convert(
                tz="US/Eastern"
            )
        except TypeError:
            stats["timestamp"] = pd.to_datetime(stats["timestamp"]).dt.tz_localize(
                tz="US/Eastern"
            )
        # Since history objects get created any time ANYTHING changes on a model, they don't necessarily represent handshakes with the API
        # So by de-duping like so:
        stats = stats.sort_values("timestamp").drop_duplicates(subset=["json"])
        # We can isolate those handshakes by filtering down to timestamps when the stats values changed
        # Which could only have occurred via an API update
        del stats["json"]
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
            if col not in ["timestamp", "json"] and col not in stats.columns:
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
                "is_private",
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

    def current_followers(self):

        try:
            followers = self.follower_lists.filter(finish_time__isnull=False).order_by(
                "-finish_time"
            )[0]
        except IndexError:
            followers = None
        return followers.followers.all()

    def current_follower_list(self):

        try:
            followers = self.follower_lists.filter(finish_time__isnull=False).order_by(
                "-finish_time"
            )[0]
        except IndexError:
            followers = None
        return followers

    def current_followings(self):

        try:
            followings = self.following_lists.filter(
                finish_time__isnull=False
            ).order_by("-finish_time")[0]
        except IndexError:
            followings = None
        return followings.followings.all()

    def current_following_list(self):

        try:
            followings = self.following_lists.filter(
                finish_time__isnull=False
            ).order_by("-finish_time")[0]
        except IndexError:
            followings = None
        return followings

    def most_recent_botometer_score(self):

        scores = self.botometer_scores.order_by("-timestamp")
        if scores.count() > 0:
            return scores[0]
        else:
            return None


class AbstractTwitterProfileSnapshot(
    with_metaclass(AbstractTwitterBase, AbstractTwitterObject)
):
    class Meta(object):
        abstract = True

    timestamp = models.DateTimeField(auto_now_add=True)

    screen_name = models.CharField(
        max_length=100, db_index=True, null=True, help_text="Twitter screen name"
    )
    name = models.CharField(max_length=200, null=True)
    contributors_enabled = models.NullBooleanField(null=True)
    description = models.TextField(null=True)
    favorites_count = models.IntegerField(null=True)
    followers_count = models.IntegerField(null=True)
    followings_count = models.IntegerField(null=True)
    is_private = models.BooleanField(default=False)
    is_verified = models.NullBooleanField(null=True)
    listed_count = models.IntegerField(null=True)
    profile_image_url = models.TextField(null=True)
    status = models.TextField(null=True)
    statuses_count = models.IntegerField(null=True)
    urls = ArrayField(models.CharField(max_length=300), default=list)
    location = models.CharField(max_length=512, null=True)
    json = JSONField(null=True, default=dict)

    """
    AUTO-CREATED RELATIONSHIPS:
    profile = models.ForeignKey(your_app.TwitterProfileModel, related_name="snapshots") 
    """

    def __str__(self):

        return "{} AS OF {}".format(str(self.profile), self.timestamp)

    @property
    def followers(self):
        follower_list = self.follower_lists.filter(finish_time__isnull=False).order_by(
            "-finish_time"
        )[0]
        return follower_list.followers.all()

    @property
    def followings(self):
        following_list = self.following_lists.filter(
            finish_time__isnull=False
        ).order_by("-finish_time")[0]
        return following_list.followings.all()

    def update_from_json(self, profile_data=None):

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
        return "http://www.twitter.com/intent/user?user_id={0}".format(
            self.twitter_id
        )  # Can we verify this? Never seen it

    def most_recent_botometer_score(self):

        scores = self.botometer_scores.order_by("-timestamp")
        if scores.count() > 0:
            return scores[0]
        else:
            return None


class AbstractTweet(with_metaclass(AbstractTwitterBase, AbstractTwitterObject)):
    class Meta(object):
        abstract = True

    created_at = models.DateTimeField(
        null=True, help_text="The time/date that the tweet was published"
    )
    links = ArrayField(
        models.CharField(max_length=400),
        default=list,
        null=True,
        help_text="Links contained in the tweet",
    )
    text = models.CharField(
        max_length=1024, null=True
    )  # Could change to 280 - no need to be so long

    profile_mentions_raw = ArrayField(
        models.CharField(max_length=280), default=list, null=True
    )

    language = models.CharField(max_length=255, null=True)

    retweet_count = models.IntegerField(null=True)
    favorite_count = models.IntegerField(null=True)

    json = JSONField(null=True, default=dict)

    """
    AUTO-CREATED RELATIONSHIPS:
    profile = models.ForeignKey(your_app.TwitterProfileModel, related_name="tweets")
    hashtags = models.ManyToManyField(your_app.TwitterHashtagModel, related_name="tweets")
    place = models.ForeignKey(your_app.TwitterPlaceModel, related_name="tweets")
    profile_mentions = models.ManyToManyField(your_app.TwitterProfileModel, related_name="tweet_mentions")
    retweeted_status = models.ForeignKey(your_app.TweetModel, related_name="retweets")
    in_reply_to_status = models.ForeignKey(your_app.TweetModel, related_name="replies")
    quoted_status = models.ForeignKey(your_app.TweetModel, related_name="quotes")
    """

    def __str__(self):

        return "{0}, {1}:\nhttps://twitter.com/{2}/status/{3}/:\n {4}".format(
            self.profile if self.profile else None,
            self.created_at,
            self.profile.screen_name if self.profile else None,
            self.twitter_id,
            decode_text(self.text),
        )

    def update_from_json(self, tweet_data=None):

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
            author = get_twitter_profile(tweet_data["user"]["id_str"], create=True)
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
                existing_profiles = TwitterProfile.objects.filter(
                    twitter_id=profile_mention["id_str"]
                )
                if existing_profiles.count() > 1:
                    print(
                        "Warning: multiple profiles found for {}".format(
                            profile_mention["id_str"]
                        )
                    )
                    print(
                        "For flexibility, Django Twitter does not enforce a unique constraint on twitter_id"
                    )
                    print(
                        "But in this case it can't tell which profile to use, so it's associating this tweet with all"
                    )
                    for existing in existing_profiles:
                        profile_mentions.append(existing)
                elif existing_profiles.count() == 1:
                    profile_mentions.append(existing_profiles[0])
                else:
                    mentioned_profile, created = TwitterProfile.objects.get_or_create(
                        twitter_id=profile_mention["id_str"]
                    )
                    profile_mentions.append(mentioned_profile)
            self.profile_mentions.set(profile_mentions)

            # HASHTAGS
            hashtags = []
            for hashtag in tweet_data.get("entities", {}).get("hashtags", []):
                hashtag_obj, created = TwitterHashtag.objects.get_or_create(
                    name=hashtag["text"].lower()
                )
                hashtags.append(hashtag_obj)
            self.hashtags.set(hashtags)

            # REPLY TO STATUS
            if tweet_data.get("in_reply_to_status_id", None):
                try:
                    tweet_obj, created = Tweet.objects.get_or_create(
                        twitter_id=tweet_data["in_reply_to_status_id_str"].lower()
                    )
                except Tweet.MultipleObjectsReturned:
                    tweet_obj = _consolidate_duplicate_tweets(
                        tweet_data["in_reply_to_status_id_str"].lower()
                    )
                tweet_obj.refresh_from_db()
                if not tweet_obj.profile and tweet_data.get(
                    "in_reply_to_user_id_str", None
                ):
                    reply_author_obj = get_twitter_profile(
                        tweet_data["in_reply_to_user_id_str"].lower(), create=True
                    )
                    tweet_obj.profile = reply_author_obj
                    tweet_obj.save()
                self.in_reply_to_status = tweet_obj

            # QUOTE STATUS
            if tweet_data.get("quoted_status", None):
                try:
                    tweet_obj, created = Tweet.objects.get_or_create(
                        twitter_id=tweet_data["quoted_status"]["id_str"].lower()
                    )
                except Tweet.MultipleObjectsReturned:
                    tweet_obj = _consolidate_duplicate_tweets(
                        tweet_data["quoted_status"]["id_str"].lower()
                    )
                tweet_obj.refresh_from_db()
                tweet_obj.update_from_json(tweet_data["quoted_status"])
                self.quoted_status = tweet_obj

            # RETWEETED STATUS
            if tweet_data.get("retweeted_status", None):
                try:
                    tweet_obj, created = Tweet.objects.get_or_create(
                        twitter_id=tweet_data["retweeted_status"]["id_str"].lower()
                    )
                except Tweet.MultipleObjectsReturned:
                    tweet_obj = _consolidate_duplicate_tweets(
                        tweet_data["retweeted_status"]["id_str"].lower()
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
                ["retweeted_status", "quoted_status", "extended_tweet"],
                ["retweeted_status"],
                ["quoted_status"],
            ]
            text_keys = ["full_text", "text"]

            def get_text(tweet_data):

                text = None
                for keys in text_patterns:
                    subset = tweet_data
                    for key in keys:
                        subset = tweet_data.get(key, {})
                    for text_key in text_keys:
                        if text_key in subset.keys():
                            text = subset[text_key]
                            break
                    if text:
                        break

                additional_text = None
                for keys in additional_text_patterns:
                    subset = tweet_data
                    for key in keys:
                        subset = tweet_data.get(key, {})
                    for text_key in text_keys:
                        if text_key in subset.keys():
                            additional_text = subset[text_key]
                            break
                    if additional_text:
                        break

                if text and additional_text:
                    # Examples of RTs: 1116460554237902849, 1116460554237902849, 1084731566423715841
                    if text.endswith("\u2026") or text.endswith("\u2026"):
                        text = re.sub(text[-1], "", text)
                        s = SequenceMatcher(None, additional_text, text, autojunk=True)
                        for block in s.get_matching_blocks():
                            if block.size > 1:
                                overlap = additional_text[
                                    block.a : (block.a + block.size)
                                ]
                                additional_text = additional_text.replace(overlap, "")
                        text = "".join([text, additional_text])

                elif not text and additional_text:
                    text = additional_text

                return text

            self.text = get_text(tweet_data)
            self.text = "{}".format(self.text)

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
        return "http://www.twitter.com/statuses/{0}".format(self.twitter_id)


class AbstractBotometerScore(with_metaclass(AbstractTwitterBase, models.Model)):
    class Meta(object):
        abstract = True

    timestamp = models.DateTimeField(auto_now_add=True)

    api_version = models.FloatField(null=True)
    error = models.CharField(max_length=100, null=True)
    automation_probability_english = models.FloatField(null=True)
    automation_probability_universal = models.FloatField(null=True)
    content_score = models.FloatField(null=True)
    friend_score = models.FloatField(null=True)
    network_score = models.FloatField(null=True)
    sentiment_score = models.FloatField(null=True)
    temporal_score = models.FloatField(null=True)
    user_score = models.FloatField(null=True)
    overall_score_english = models.FloatField(null=True)
    overall_score_universal = models.FloatField(null=True)

    json = JSONField(null=True, default=dict)

    """
    AUTO-CREATED RELATIONSHIPS:
    profile = models.ForeignKey(your_app.TwitterProfileModel, related_name="botometer_scores")
    """

    def update_from_json(self, score_data=None, api_version=None):

        if not score_data:
            self.error = "No data"
        if score_data:
            self.automation_probability_english = score_data.get("cap", {}).get(
                "english", 0
            )
            self.automation_probability_universal = score_data.get("cap", {}).get(
                "universal", 0
            )
            self.content_score = score_data.get("display_scores", {}).get("content", 0)
            self.friend_score = score_data.get("display_scores", {}).get("friend", 0)
            self.network_score = score_data.get("display_scores", {}).get("network", 0)
            self.sentiment_score = score_data.get("display_scores", {}).get(
                "sentiment", 0
            )
            self.temporal_score = score_data.get("display_scores", {}).get(
                "temporal", 0
            )
            self.user_score = score_data.get("display_scores", {}).get("user", 0)
            self.overall_score_english = score_data.get("display_scores", {}).get(
                "english", 0
            )
            self.overall_score_universal = score_data.get("display_scores", {}).get(
                "universal", 0
            )
            self.json = score_data
            if api_version:
                self.api_version = api_version
            self.save()


class AbstractTwitterFollowerList(with_metaclass(AbstractTwitterBase, models.Model)):
    class Meta(object):
        abstract = True

    # profile = models.ForeignKey("TwitterProfile", related_name="follower_lists")
    # followers = models.ManyToManyField("TwitterProfile", related_name=None)
    start_time = models.DateTimeField(auto_now_add=True)
    finish_time = models.DateTimeField(null=True)


class AbstractTwitterFollowingList(with_metaclass(AbstractTwitterBase, models.Model)):
    class Meta(object):
        abstract = True

    # profile = models.ForeignKey("TwitterProfile", related_name="following_lists")
    # followings = models.ManyToManyField("TwitterProfile", related_name=None)
    start_time = models.DateTimeField(auto_now_add=True)
    finish_time = models.DateTimeField(null=True)


class AbstractTwitterHashtag(with_metaclass(AbstractTwitterBase, models.Model)):
    class Meta(object):
        abstract = True

    name = models.CharField(max_length=150, unique=True, db_index=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        super(AbstractTwitterHashtag, self).save(*args, **kwargs)


####
# Additional classes that are in Rookery that I don't think we need
class AbstractTwitterPlace(with_metaclass(AbstractTwitterBase, AbstractTwitterObject)):
    class Meta(object):
        abstract = True

    full_name = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    place_type = models.CharField(max_length=255)
    country_code = models.CharField(max_length=10)
    country = models.CharField(max_length=255)

    def save(self, *args, **kwargs):

        if not all([self.name, self.place_type] or kwargs.get("reparse", False)):
            self.place_type = self.json["place_type"]
            self.country = self.json["country"]
            self.name = self.json["name"]
            self.full_name = self.json["full_name"]
        super(AbstractTwitterPlace, self).save(*args, **kwargs)


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
    class Meta(object):
        abstract = True

    name = models.CharField(max_length=256, unique=True)

    """
    AUTO-CREATED RELATIONSHIPS:
    tweets = models.ManyToManyField(your_app.TweetModel, related_name="tweet_sets")
    """

    def __str__(self):

        return self.name


class AbstractTwitterProfileSet(with_metaclass(AbstractTwitterBase, models.Model)):
    class Meta(object):
        abstract = True

    name = models.CharField(max_length=256, unique=True)

    """
    AUTO-CREATED RELATIONSHIPS:
    profiles = models.ManyToManyField(your_app.TwitterProfileModel, related_name="twitter_profile_sets")
    """

    def __str__(self):

        return self.name


if settings.TWITTER_APP == "django_twitter":

    class TwitterProfile(AbstractTwitterProfile):
        pass

    class TwitterProfileSnapshot(AbstractTwitterProfileSnapshot):
        pass

    class Tweet(AbstractTweet):
        pass

    class BotometerScore(AbstractBotometerScore):
        pass

    class TwitterHashtag(AbstractTwitterHashtag):
        pass

    class TwitterPlace(AbstractTwitterPlace):
        pass

    class TweetSet(AbstractTweetSet):
        pass

    class TwitterProfileSet(AbstractTwitterProfileSet):
        pass
