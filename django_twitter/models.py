from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField
from picklefield.fields import PickledObjectField
from simple_history.models import HistoricalRecords
from dateutil.parser import parse as date_parse

from django_commander.models import LoggedExtendedModel
from pewtils import decode_text, is_not_null, is_null


class TwitterProfile(LoggedExtendedModel):

    twitter_id = models.CharField(max_length=150, db_index=True, help_text="The Twitter account ID")

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

    botometer_content = models.FloatField(null=True)
    botometer_friend = models.FloatField(null=True)
    botometer_network = models.FloatField(null=True)
    botometer_sentiment = models.FloatField(null=True)
    botometer_temporal = models.FloatField(null=True)
    botometer_user = models.FloatField(null=True)
    botometer_scores_english = models.FloatField(null=True)
    botometer_scores_universal = models.FloatField(null=True)
    
    historical = models.BooleanField(default=False)

    json = JSONField(null=True, default=dict)

    history = HistoricalRecords()

    followers = models.ManyToManyField("django_twitter.TwitterProfile", related_name="friends", through="django_twitter.TwitterFollow",
                                       symmetrical=False)
    
    def __str__(self):
        
        return self.screen_name

    def save(self, *args, **kwargs):

        if self.twitter_id:
            self.twitter_id = str(self.twitter_id).lower()
        super(TwitterProfile, self).save(*args, **kwargs)

    def update_from_json(self, profile_data=None):

        if not profile_data:
            profile_data = self.json
        if profile_data:
            self.created_at = date_parse(profile_data['created_at'])
            self.screen_name = profile_data['screen_name'].lower()
            self.description = profile_data['description'],
            self.favorites_count = profile_data['favorites_count'] if "favorites_count" in profile_data.keys() else \
            profile_data['favourites_count']
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
            self.urls = [url['expanded_url'] for url in profile_data['entities']['url']['urls'] if
                         url['expanded_url']] if "url" in profile_data['entities'].keys() else []
            self.save()

    def url(self):
        return "http://www.twitter.com/intent/user?user_id={0}".format(self.twitter_id)


class Tweet(LoggedExtendedModel):

    profile = models.ForeignKey("django_twitter.TwitterProfile", related_name="tweets", help_text="The parent Twitter profile")
    twitter_id = models.CharField(max_length=200, db_index=True, unique=True, help_text="Uses the unique identifier provided \
        by Twitter")

    timestamp = models.DateTimeField(null=True, help_text="The time/date that the tweet was published")
    links = ArrayField(models.CharField(max_length=400), default=[], null=True,
                       help_text="Links contained in the tweet")

    retweeted = models.NullBooleanField(null=True)
    favorited = models.NullBooleanField(null=True)
    retweet_count = models.IntegerField(null=True)
    favorite_count = models.IntegerField(null=True)

    user_mentions = models.ManyToManyField("django_twitter.TwitterProfile", related_name="tweet_mentions")
    hashtags = models.ManyToManyField("django_twitter.TwitterHashtag", related_name="tweets")

    json = PickledObjectField(null=True)

    last_update_time = models.DateTimeField(auto_now=True, null=True,
                                            help_text="The last time the tweet was updated from the API"
                                            )

    history = HistoricalRecords()

    def __str__(self):

        return "{0}, {1}: {2}".format(
            self.profile,
            self.timestamp,
            decode_text(self.document.text) if self.document and self.document.text else None
        )

    def save(self, *args, **kwargs):

        if self.twitter_id:
            self.twitter_id = str(self.twitter_id).lower()
        super(Tweet, self).save(*args, **kwargs)

    def update_from_json(self, tweet_data=None):

        if not tweet_data:
            tweet_data = self.json
        if tweet_data:

            self.timestamp = date_parse(tweet_data['created_at'])
            self.retweet_count = tweet_data.get("retweet_count", None)
            self.favorite_count = tweet_data.get("favorite_count", None)
            self.retweeted = tweet_data.get("retweeted", None)
            self.favorited = tweet_data.get("favorited", None)

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

            if self.pk:

                user_mentions = []
                for user_mention in tweet_data["entities"]["user_mentions"]:
                    existing_profiles = TwitterProfile.objects.filter(twitter_id=user_mention["id_str"])
                    if existing_profiles.count() > 1:
                        # print "This tweet mentioned an ID that belongs to multiple profiles"
                        # # TODO: you probably want to just try filtering on historical=False at this point
                        # # for now, since this is so rare, we'll just add all the possibilities
                        # import pdb
                        # pdb.set_trace()
                        for existing in existing_profiles:
                            user_mentions.append(existing)
                    elif existing_profiles.count() == 1:
                        user_mentions.append(existing_profiles[0])
                    else:
                        user_mentions.append(
                            TwitterProfile.objects.create(
                                twitter_id=user_mention["id_str"],
                                historical=False
                            )
                        )
                self.user_mentions = user_mentions

                hashtags = []
                for hashtag in tweet_data["entities"]["hashtags"]:
                    hashtags.append(TwitterHashtag.objects.create_or_update({"name": hashtag["text"].lower()}))
                self.hashtags = hashtags

            self.save()

    def url(self):
        return "http://www.twitter.com/statuses/{0}".format(self.twitter_id)


class TwitterFollow(LoggedExtendedModel):
    
    friend = models.ForeignKey("django_twitter.TwitterProfile", related_name="follower_details")
    follower = models.ForeignKey("django_twitter.TwitterProfile", related_name="friend_details")
    dates = ArrayField(models.DateField(), default=[])

    class Meta:
        unique_together = ("friend", "follower")

    def __str__(self):
        return "{} following {}".format(self.follower, self.friend)


class TwitterHashtag(LoggedExtendedModel):
    name = models.CharField(max_length=150, unique=True, db_index=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        super(TwitterHashtag, self).save(*args, **kwargs)