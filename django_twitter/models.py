import re

from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField
from django.utils import timezone
from picklefield.fields import PickledObjectField
from simple_history.models import HistoricalRecords
from dateutil.parser import parse as date_parse
from datetime import datetime

from pewtils import decode_text, is_not_null, is_null


class AbstractTwitterBase(models.base.ModelBase):

    class Meta:
        abstract = True

    def __new__(cls, name, bases, attrs):

        model = super(AbstractTwitterBase, cls).__new__(cls, name, bases, attrs)

        for base in bases:
            model_name = re.sub('Abstract', '', base.__name__) + 'Model'
            if base.__module__.startswith("django_twitter"):
                setattr(cls, model_name, model)

            throughs = ["TwitterRelationshipModel"]
            for relationship_type, owner_model, related_model, field_name, related_name, through, symmetrical in [
                (models.ForeignKey, "TweetModel", "TwitterProfileModel", "profile", "tweets", None, True),
                (models.ForeignKey, "BotometerScoreModel", "TwitterProfileModel", "profile", "botometer_scores", None, True),
                (models.ManyToManyField, "TweetModel", "TwitterHashtagModel", "tweets", "hashtags", None, True),
                (models.ForeignKey, "TweetModel", "TwitterPlaceModel", "place", "tweets", None, True),
                (models.ManyToManyField, "TweetModel", "TwitterProfileModel", "tweet_mentions", "user_mentions", None, True),
                (models.ForeignKey, "TwitterRelationshipModel", "TwitterProfileModel", "friend", "follower_details", None, True),
                (models.ForeignKey, "TwitterRelationshipModel", "TwitterProfileModel", "follower", "friend_details", None, True),
                (models.ManyToManyField, "TwitterProfileModel", "TwitterProfileModel", "followers", "friends", "TwitterRelationshipModel", False),

            ]:
                # if owner_model == "TwitterRelationshipModel" and hasattr(cls, owner_model):
                #     import pdb
                #     pdb.set_trace()

                if hasattr(cls, owner_model) and hasattr(cls, related_model) \
                        and getattr(cls, owner_model) and getattr(cls, related_model) and \
                        (not through or (hasattr(cls, through) and getattr(cls, through))):
                    try:
                        getattr(cls, owner_model)._meta.get_field(field_name)
                    except models.fields.FieldDoesNotExist:
                        field_params = {"related_name": related_name}
                        if through:
                            field_params["through"] = getattr(cls, through)
                        if not symmetrical:
                            field_params["symmetrical"] = symmetrical
                        if relationship_type != models.ManyToManyField and owner_model not in throughs:
                            field_params["null"] = True
                        getattr(cls, owner_model).add_to_class(
                            field_name,
                            relationship_type(
                                getattr(cls, related_model),
                                **field_params
                            )
                        )

            return model


class AbstractTwitterObject(models.Model):

    twitter_id = models.CharField(max_length=150, db_index=True)
    last_update_time = models.DateTimeField(auto_now=True)
    historical = models.BooleanField(default=False)
    history = HistoricalRecords()
    # TODO: add historical_twitter_ids

    def save(self, *args, **kwargs):
        self.twitter_id = str(self.twitter_id).lower()
        self.last_update_time = timezone.now()
        super(AbstractTwitterObject, self).save(*args, **kwargs)


class AbstractTwitterProfile(AbstractTwitterObject):

    class Meta:
        abstract = True

    __metaclass__ = AbstractTwitterBase

    tweet_backfilled = models.BooleanField(default=False,
                                         help_text="An indicator used in the sync_tweets management function; True indicates that the user's \
        tweet history has been backfilled as far as possible, so the sync function will stop after it hits an existing \
        tweet the next time it runs.")

    screen_name = models.CharField(max_length=100, db_index=True, null=True, help_text="Twitter screen name")
    name = models.CharField(max_length=200, null=True)
    description = models.TextField(null=True)
    status = models.TextField(null=True)
    urls = ArrayField(models.CharField(max_length=300), default=[])
    contributors_enabled = models.NullBooleanField(null=True)
    is_verified = models.NullBooleanField(null=True)
    created_at = models.DateTimeField(null=True)
    profile_image_url = models.TextField(null=True)

    ### Added from Rookery
    geo_enabled = models.NullBooleanField()
    # We're going to need to see what we need to do to be compliant with the GDPR here
    location = models.CharField(max_length = 512, null = True) # 256 in Dippybird
    language = models.CharField(max_length = 255, null = True) # I DON'T THINK THIS IS NECESSARY
    # may not need both of these
    time_zone = models.CharField(max_length = 255, null = True) # not sure if this will still be in API
    utc_offset = models.CharField(max_length = 255, null = True) # not sure this needs to be a charfield.

    favorites_count = models.IntegerField(null=True)
    followers_count = models.IntegerField(null=True)
    friends_count = models.IntegerField(null=True)
    listed_count = models.IntegerField(null=True)
    statuses_count = models.IntegerField(null=True)

    json = JSONField(null=True, default=dict)

    def __str__(self):
        
        return self.screen_name # Can this include some more info? I've in the past included the constructed the URL

    def save(self, *args, **kwargs):

        if self.twitter_id:
            self.twitter_id = str(self.twitter_id).lower()
        super(AbstractTwitterProfile, self).save(*args, **kwargs)

    def update_from_json(self, profile_data=None):

        if not profile_data:
            profile_data = self.json
        if profile_data:
            # TODO: Last step - Verify that all of the fields above are in here
            self.created_at = date_parse(profile_data['created_at'])
            self.screen_name = profile_data['screen_name'].lower()
            self.description = profile_data['description'],
            self.favorites_count = profile_data['favorites_count'] if "favorites_count" in profile_data.keys() else \
                profile_data['favourites_count']
            self.followers_count = profile_data['followers_count']
            self.friends_count = profile_data['friends_count']
            self.listed_count = profile_data['listed_count']
            self.language = profile_data['language']
            self.statuses_count = profile_data['statuses_count']
            self.profile_image_url = profile_data['profile_image_url']
            self.status = profile_data['status']['text'] if 'status' in profile_data.keys() else None
            self.is_verified = profile_data['verified']
            self.contributors_enabled = profile_data['contributors_enabled']
            self.urls = [url['expanded_url'] for url in profile_data['entities']['url']['urls'] if
                         url['expanded_url']] if "url" in profile_data['entities'].keys() else []
            self.save()

    def url(self):
        return "http://www.twitter.com/intent/user?user_id={0}".format(self.twitter_id) # Can we verify this? Never seen it


class AbstractTweet(AbstractTwitterObject):

    class Meta:
        abstract = True

    __metaclass__ = AbstractTwitterBase

    # Rookery calls this created_at - I think that would be good for consistency
    created_at = models.DateTimeField(null=True, help_text="The time/date that the tweet was published")
    links = ArrayField(models.CharField(max_length=400), default=[], null=True,
                       help_text="Links contained in the tweet")

    # Added from Rookery
    in_reply_to_screen_name = models.CharField(max_length=255, null=True)
    in_reply_to_status_id = models.CharField(max_length=255, null=True)
    in_reply_to_user_id = models.CharField(max_length=255, null=True)
    language = models.CharField(max_length=255, null=True)
    # latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    # longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    quoted_status_id = models.CharField(max_length=255, null=True)
    # source = type of device. Removing this because it seems like it would be rarely used (will be in the json)
    #source = models.CharField(max_length=255, null=True)
    text = models.CharField(max_length = 1024, null = True) # Could change to 280 - no need to be so long

    retweeted = models.NullBooleanField(null=True)
    favorited = models.NullBooleanField(null=True)
    retweet_count = models.IntegerField(null=True)
    favorite_count = models.IntegerField(null=True)

    json = PickledObjectField(null=True)

    def __str__(self):

        return "{0}, {1}: {2}".format(
            self.profile,
            self.timestamp,
            decode_text(self.document.text) if self.document and self.document.text else None # I don't understand this business
        )

    def update_from_json(self, tweet_data=None):

        if not tweet_data:
            tweet_data = self.json
        if tweet_data:
            # TODO: Update with any new fields

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
                    existing_profiles = AbstractTwitterProfile.objects.filter(twitter_id=user_mention["id_str"])
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
                            AbstractTwitterProfile.objects.create(
                                twitter_id=user_mention["id_str"],
                                historical=False
                            )
                        )
                self.user_mentions = user_mentions

                hashtags = []
                for hashtag in tweet_data["entities"]["hashtags"]:
                    hashtags.append(AbstractTwitterHashtag.objects.create_or_update({"name": hashtag["text"].lower()}))
                self.hashtags = hashtags

            self.save()

    def url(self):
        return "http://www.twitter.com/statuses/{0}".format(self.twitter_id)


class AbstractBotometerScore(models.Model):

    class Meta:
        abstract = True

    __metaclass__ = AbstractTwitterBase

    timestamp = models.DateTimeField(auto_now_add=True)

    api_version = models.FloatField(null=True)
    botometer_content = models.FloatField(null=True)
    botometer_friend = models.FloatField(null=True)
    botometer_network = models.FloatField(null=True)
    botometer_sentiment = models.FloatField(null=True)
    botometer_temporal = models.FloatField(null=True)
    botometer_user = models.FloatField(null=True)
    botometer_scores_english = models.FloatField(null=True)
    botometer_scores_universal = models.FloatField(null=True)


class AbstractTwitterRelationship(models.Model):

    class Meta:
        abstract = True

    __metaclass__ = AbstractTwitterBase

    dates = ArrayField(models.DateField(), default=[])

    def __str__(self):
        return "{} following {}".format(self.follower, self.friend)


class AbstractTwitterHashtag(models.Model):

    class Meta:
        abstract = True

    __metaclass__ = AbstractTwitterBase

    name = models.CharField(max_length=150, unique=True, db_index=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        super(AbstractTwitterHashtag, self).save(*args, **kwargs)

####
# Additional classes that are in Rookery that I don't think we need
class AbstractTwitterPlace(AbstractTwitterObject):

    class Meta:
        abstract = True

    __metaclass__ = AbstractTwitterBase

    full_name = models.CharField(max_length = 255)
    name = models.CharField(max_length = 255)
    place_type = models.CharField(max_length = 255)
    country_code = models.CharField(max_length = 10)
    country = models.CharField(max_length = 255)

    def save(self, *args, **kwargs):

        if not all([self.name, self.place_type] or kwargs.get("reparse", False)):
            self.place_type = self.json["place_type"]
            self.country = self.json["country"]
            self.name = self.json["name"]
            self.full_name = self.json["full_name"]
        super(AbstractTwitterPlace, self).save(*args, **kwargs)