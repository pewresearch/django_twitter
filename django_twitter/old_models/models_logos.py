from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField
from picklefield.fields import PickledObjectField
from simple_history.models import HistoricalRecords
from dateutil.parser import parse as date_parse

from pewtils.django.abstract_models import BasicExtendedModel
from django_commander.models import LoggedExtendedModel
from django_verifications.models import VerifiedModel
from django_verifications.managers import VerifiedModelManager
from django_queries.models import QueryModel
from django_queries.managers import QueryModelManager

from logos.models.managers.media import *
from pewtils import decode_text, is_not_null, is_null
from pewtils.django import get_model
from pewtils.facebook import FacebookAPIHandler


class TwitterProfile(VerifiedModel, LoggedExtendedModel, QueryModel):

    """
    A Twitter profile for a politician or campaign, uniquely identified by the twitter_id.  The backfill flag indicates
    whether or not the tweet loader has iterated as far back as it can go.
    """

    twitter_id = models.CharField(max_length=150, db_index=True, help_text="The Twitter account ID")
    politician = models.ForeignKey("logos.Politician", related_name="twitter_profiles", null=True, blank=True,
                                   on_delete=models.SET_NULL, help_text="The politician that tweeted")

    tweet_backfill = models.BooleanField(default=False,
                                         help_text="An indicator used in the sync_tweets management function; True indicates that the politician's \
        tweet history has been backfilled as far as possible, so the sync function will stop after it hits an existing \
        tweet the next time it runs.")

    screen_name = models.CharField(max_length=100, db_index=True, null=True, help_text="Twitter screen name")
    name = models.CharField(max_length=200, null=True)
    location = models.TextField(null=True)
    description = models.TextField(null=True)
    status = models.TextField(null=True)
    urls = ArrayField(models.CharField(max_length=300), default=[])
    contributors_enabled = models.NullBooleanField(null=True)
    is_verified = models.NullBooleanField(null=True)
    created_at = models.DateTimeField(null=True)
    profile_image_url = models.TextField(null=True)

    favorites_count = models.IntegerField(null=True)
    followers_count = models.IntegerField(null=True)
    friends_count = models.IntegerField(null=True)
    listed_count = models.IntegerField(null=True)
    statuses_count = models.IntegerField(null=True)

    is_official = models.NullBooleanField(null=True)
    historical = models.BooleanField(default=False)

    json = JSONField(null=True, default=dict)

    history = HistoricalRecords()

    objects = type("MergedTwitterProfileManager", (QueryModelManager, VerifiedModelManager), {})().as_manager()

    friends = models.ManyToManyField("logos.TwitterProfile", related_name="followers", through="logos.TwitterFollow", symmetrical=False)

    class Meta:

        unique_together = ("twitter_id", "politician")

        fields_to_verify = [
            "politician", "is_official"
        ]

        verification_filters = [
            {"politician__isnull": False}
        ]

    def __str__(self):

        if self.politician: owner = str(self.politician)
        else: owner = "unknown"

        return "%s (%s)" % (self.screen_name if self.screen_name else self.twitter_id, owner)

    def save(self, *args, **kwargs):

        if self.twitter_id: self.twitter_id = str(self.twitter_id).lower()
        if self.json:
            profile_data = self.json
            self.screen_name = profile_data['screen_name'].lower()
            self.description = profile_data['description'],
            self.favorites_count = profile_data['favorites_count'] if "favorites_count" in profile_data.keys() else profile_data['favourites_count']
            self.followers_count = profile_data['followers_count']
            self.friends_count = profile_data['friends_count']
            self.listed_count = profile_data['listed_count']
            self.location = profile_data['location']
            self.name = profile_data['name']
            self.profile_image_url = profile_data['profile_image_url']
            self.statuses_count = profile_data['statuses_count']
            self.status = profile_data['status']['text'] if 'status' in profile_data.keys() else None
            self.is_verified = profile_data['verified']
            self.contributors_enabled = profile_data['contributors_enabled']
            self.urls = [url['expanded_url'] for url in profile_data['entities']['url']['urls'] if url['expanded_url']] if "url" in profile_data['entities'].keys() else []
        super(TwitterProfile, self).save(*args, **kwargs)

    def update_tweets_official_status(self):

        if self.politician:
            self.tweets.update(is_official=False)
            if self.is_official:
                for term in self.politician.terms.all():
                    self.tweets \
                        .filter(timestamp__gte=term.start_date) \
                        .filter(timestamp__lte=term.end_date) \
                        .update(is_official=True)

    def url(self): return "http://www.twitter.com/intent/user?user_id={0}".format(self.twitter_id)

    def get_verification_metadata(self):

        if hasattr(self, "politician") and self.politician:
            latest_term = self.politician.latest_term
            if not latest_term:
                campaigns = self.politician.campaigns.order_by("-election__year")
                if campaigns.count() > 0:
                    pol_text = " --- latest campaign: {}".format(str(campaigns[0]))
                else:
                    pol_text = " --- NO TERMS OR CAMPAIGNS FOUND"
            else:
                pol_text = " --- latest term: {}".format(str(latest_term))
        else:
            pol_text = ""

        return {
            "twitter_id": self.twitter_id,
            "name": self.name,
            "screen_name": self.screen_name,
            "location": self.location,
            "description": self.description,
            "status": self.status,
            "urls": self.urls,
            "politician": str(self.politician) + pol_text
        }


class Tweet(LoggedExtendedModel, QueryModel):

    """
    This model contains tweets created by members of Congress and/or campaigns.  The management command
    :mod:`logos.management.subcommands.load.twitter_politician_tweets` can be used to download the latest batch
    of tweets for all politicians with known Twitter IDs.  Tweets are linked back to an originating TwitterProfile
    object.
    """

    profile = models.ForeignKey("logos.TwitterProfile", related_name="tweets", help_text="The parent Twitter profile")
    twitter_id = models.CharField(max_length=200, db_index=True, unique=True, help_text="Uses the unique identifier provided \
        by Twitter")

    timestamp = models.DateTimeField(help_text="The time/date that the tweet was published")
    year = models.ForeignKey("logos.Year", related_name="tweets", null=True, on_delete=models.SET_NULL,
                             help_text="The year the tweet was published")
    links = ArrayField(models.CharField(max_length=400), default=[], null=True,
                       help_text="Links contained in the tweet")

    retweet_count = models.IntegerField(null=True)
    favorite_count = models.IntegerField(null=True)

    user_mentions = models.ManyToManyField("logos.TwitterProfile", related_name="tweet_mentions")
    hashtags = models.ManyToManyField("logos.TwitterHashtag", related_name="tweets")

    json = PickledObjectField(null=True)

    last_update_time = models.DateTimeField(auto_now=True, null=True,
                                            help_text="The last time the tweet was updated from the API"
                                            )

    is_official = models.NullBooleanField(null=True)

    document = models.OneToOneField("django_learning.Document", related_name="tweet", null=True)

    history = HistoricalRecords()

    def __str__(self):

        return "{0}, {1}: {2}".format(
            self.profile.politician,
            self.timestamp,
            decode_text(self.document.text) if self.document and self.document.text else None
        )

    def save(self, *args, **kwargs):

        if self.twitter_id: self.twitter_id = str(self.twitter_id).lower()
        if self.json:

            tweet_data = self.json

            self.retweet_count = tweet_data.get("retweet_count", None)
            self.favorite_count = tweet_data.get("favorite_count", None)

            try:
                links = set(self.links)
            except TypeError:
                links = set()
            for u in tweet_data.get("entities", {}).get("urls", []):
                link = u.get("expanded_url", "")
                if len(link) > 399: link = u.get("url", "")
                if is_not_null(link):
                    links.add(link)
            self.links = list(links)

            user_mentions = []
            for user_mention in tweet_data["entities"]["user_mentions"]:
                user_mentions.append(
                    TwitterProfile.objects.create_or_update({"twitter_id": user_mention["id_str"], "historical": False})
                )
            self.user_mentions = user_mentions

            hashtags = []
            for hashtag in tweet_data["entities"]["hashtags"]:
                hashtags.append(TwitterHashtag.objects.create_or_update({"name": hashtag["text"]}))
            self.hashtags = hashtags

        if is_null(self.is_official):
            self.is_official = self.get_official_status()

        super(Tweet, self).save(*args, **kwargs)

    def get_official_status(self):

        is_official = False
        if self.profile.politician and self.profile.is_official:
            for term in self.profile.politician.terms.all():
                if self.timestamp >= term.start_date and self.timestamp <= term.end_date:
                    is_official = True
                    break
        return is_official

    def url(self): return "http://www.twitter.com/statuses/{0}".format(self.twitter_id)
    
    
class TwitterFollow(LoggedExtendedModel, QueryModel):

    friend = models.ForeignKey("logos.TwitterProfile", related_name="follower_details")
    follower = models.ForeignKey("logos.TwitterProfile", related_name="friend_details")
    dates = models.ManyToManyField("logos.Date", related_name="twitter_follows")

    class Meta:

        unique_together = ("friend", "follower")

    def __str__(self):

        return "{} following {}".format(self.follower, self.friend)


class TwitterHashtag(LoggedExtendedModel, QueryModel):

    name = models.CharField(max_length=150, unique=True, db_index=True)

    def __str__(self):

        return self.name