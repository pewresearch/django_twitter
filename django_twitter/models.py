from __future__ import print_function
from builtins import str
from builtins import object
import re
import simple_history

from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField
from django.utils import timezone
from django.conf import settings
from django.apps import apps

from picklefield.fields import PickledObjectField
from simple_history import register
from simple_history.models import HistoricalRecords
from dateutil.parser import parse as date_parse
from datetime import datetime
from collections import defaultdict

from pewtils import decode_text, is_not_null, is_null
from future.utils import with_metaclass


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
            model_name = re.sub('Abstract', '', base.__name__) + 'Model'
            if base.__module__.startswith("django_twitter"):
                setattr(cls, model_name, model)

        counts = defaultdict(int)
        fields_to_add = {
            "TweetModel": [
                (models.ForeignKey, "TwitterProfileModel", "profile", "tweets", None, True, models.CASCADE),
                (models.ManyToManyField, "TwitterHashtagModel", "hashtags", "tweets", None, True, None),
                (models.ForeignKey, "TwitterPlaceModel", "place", "tweets", None, True, models.SET_NULL),
                (models.ManyToManyField, "TwitterProfileModel", "user_mentions", "tweet_mentions", None, True, None),
                (models.ForeignKey, "TweetModel", "retweeted_status", "retweets", None, True, models.SET_NULL),
                (models.ForeignKey, "TweetModel", "in_reply_to_status", "replies", None, True, models.SET_NULL),
                (models.ForeignKey, "TweetModel", "quoted_status", "quotes", None, True, models.SET_NULL)
            ],
            "BotometerScoreModel": [
                (models.ForeignKey, "TwitterProfileModel", "profile", "botometer_scores", None, True, models.CASCADE)
            ],
            "TwitterRelationshipModel": [
                (models.ForeignKey, "TwitterProfileModel", "following", "follower_details", None, True, models.CASCADE),
                (models.ForeignKey, "TwitterProfileModel", "follower", "following_details", None, True, models.CASCADE)
            ],
            "TwitterProfileModel": [
                (models.ManyToManyField, "TwitterProfileModel", "followers", "followings", "TwitterRelationshipModel", False, None)
            ],
            "TweetSetModel": [
                (models.ManyToManyField, "TweetModel", "tweets", "tweet_sets", None, True, None)
            ],
            "TwitterProfileSetModel": [
                (models.ManyToManyField, "TwitterProfileModel", "profiles", "twitter_profile_sets", None, True, None)
            ]
        }
        throughs = ["TwitterRelationshipModel"]
        for owner_model in list(fields_to_add.keys()):
            for relationship_type, related_model, field_name, related_name, through, symmetrical, on_delete in fields_to_add[owner_model]:

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
                        if is_not_null(on_delete):
                            getattr(cls, owner_model).add_to_class(
                                field_name,
                                relationship_type(
                                    getattr(cls, related_model),
                                    on_delete,
                                    **field_params
                                )
                            )
                        else:
                            getattr(cls, owner_model).add_to_class(
                                field_name,
                                relationship_type(
                                    getattr(cls, related_model),
                                    **field_params
                                )
                            )
                    counts[owner_model] += 1
                    if counts[owner_model] == len(fields_to_add[owner_model]):
                        if getattr(cls, owner_model).__base__.__base__.__name__ == "AbstractTwitterObject":
                            try:
                                history = HistoricalRecords()
                                history.contribute_to_class(getattr(cls, owner_model), "history")
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


class AbstractTwitterProfile(with_metaclass(AbstractTwitterBase, AbstractTwitterObject)):

    class Meta(object):
        abstract = True


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
    is_private = models.BooleanField(default=False)
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
    followings_count = models.IntegerField(null=True)
    listed_count = models.IntegerField(null=True)
    statuses_count = models.IntegerField(null=True)

    twitter_error_code = models.IntegerField(null=True)

    json = JSONField(null=True, default=dict)

    """
    AUTO-CREATED RELATIONSHIPS:
    followers = models.ManyToManyField(your_app.TwitterProfileModel, related_name="followings") 
    """

    def __str__(self):

        return str("{0}: http://twitter.com/{0}".format(self.screen_name) if self.screen_name else self.twitter_id)

    def update_from_json_gnip(self, profile_data):
        profile_data = profile_data['actor']
        self.twitter_id = profile_data['id']
        self.created_at = date_parse(profile_data['postedTime'])
        self.screen_name = profile_data['preferredUsername'].lower()
        self.description = profile_data['summary']
        # Not sure if the if statement below is ever called
        self.favorites_count = profile_data['favoritesCount'] if "favorites_count" in list(profile_data.keys()) else \
            profile_data['favouritesCount']
        self.followers_count = profile_data['followersCount']
        self.followings_count = profile_data['friendsCount']
        self.listed_count = profile_data['listedCount']
        self.language = profile_data['language']
        self.statuses_count = profile_data['statusesCount']
        self.profile_image_url = profile_data['image']
        self.is_verified = profile_data['verified']
        # Below is not in gnip
        #self.status = profile_data['status']['text'] if 'status' in profile_data.keys() else None
        self.contributors_enabled = profile_data['contributors_enabled']
        self.urls = [link['href'] for link in profile_data['links']]
        # self.urls = [url['expanded_url'] for url in profile_data.get('entities', {}).get('url', {}).get('urls', []) if
        #              url['expanded_url']] if "url" in profile_data.get('entities', {}).keys() else profile_data.get(
        #     'url', '')
        self.json = profile_data
        self.save()

    def update_from_json(self, profile_data=None):

        if not profile_data:
            profile_data = self.json
        if profile_data:
            # TODO: Last step - Verify that all of the fields above are in here
            self.created_at = date_parse(profile_data['created_at'])
            self.screen_name = profile_data['screen_name'].lower()
            self.description = profile_data['description']
            self.favorites_count = profile_data['favorites_count'] if "favorites_count" in list(profile_data.keys()) else \
                profile_data['favourites_count']
            self.followers_count = profile_data['followers_count']
            self.followings_count = profile_data['friends_count']
            self.listed_count = profile_data['listed_count']
            self.language = profile_data['lang']
            self.statuses_count = profile_data['statuses_count']
            self.profile_image_url = profile_data['profile_image_url']
            self.status = profile_data['status']['text'] if 'status' in list(profile_data.keys()) else None
            self.is_verified = profile_data['verified']
            self.contributors_enabled = profile_data['contributors_enabled']
            self.urls = [url['expanded_url'] for url in profile_data.get('entities', {}).get('url', {}).get('urls', []) if
                         url['expanded_url']] if "url" in list(profile_data.get('entities', {}).keys()) else profile_data.get('url', '')
            if self.urls == None or self.urls=='':
                self.urls = []
            self.json = profile_data
            self.save()

    def url(self):
        return "http://www.twitter.com/intent/user?user_id={0}".format(self.twitter_id) # Can we verify this? Never seen it

    def current_followers(self):

        try: max_run = self.follower_details.order_by("-run_id")[0].run_id
        except IndexError: max_run = None
        follower_ids = self.follower_details.filter(run_id=max_run).values_list("follower_id", flat=True)
        return self.followers.filter(pk__in=follower_ids).distinct()

    def current_followings(self):

        try: max_run = self.following_details.order_by("-run_id")[0].run_id
        except IndexError: max_run = None
        following_ids = self.following_details.filter(run_id=max_run).values_list("following_id", flat=True)
        return self.followings.filter(pk__in=following_ids).distinct()

    def most_recent_botometer_score(self):

        scores = self.botometer_scores.order_by("-timestamp")
        if scores.count() > 0:
            return scores[0]
        else:
            return None


class AbstractTweet(with_metaclass(AbstractTwitterBase, AbstractTwitterObject)):

    class Meta(object):
        abstract = True


    # Rookery calls this created_at - I think that would be good for consistency
    created_at = models.DateTimeField(null=True, help_text="The time/date that the tweet was published")
    links = ArrayField(models.CharField(max_length=400), default=[], null=True,
                       help_text="Links contained in the tweet")
    text = models.CharField(max_length = 1024, null = True) # Could change to 280 - no need to be so long
    # hashtags = ArrayField(models.CharField(max_length=280), default = [], null=True)
    # TODO: Change below to a relationship
    # user_mentions = models.ManyToManyField("")
    user_mentions_raw = ArrayField(models.CharField(max_length=280), default=[], null=True)

    language = models.CharField(max_length=255, null=True)

    retweet_count = models.IntegerField(null=True)
    favorite_count = models.IntegerField(null=True)

    json = JSONField(null=True, default=dict)

    # latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    # longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True)

    # source = type of device. Removing this because it seems like it would be rarely used (will be in the json)
    # source = models.CharField(max_length=255, null=True)

    """
    AUTO-CREATED RELATIONSHIPS:
    profile = models.ForeignKey(your_app.TwitterProfileModel, related_name="tweets") 
    hashtags = models.ManyToManyField(your_app.TwitterHashtagModel, related_name="tweets")
    place = models.ForeignKey(your_app.TwitterPlaceModel, related_name="tweets")
    user_mentions = models.ManyToManyField(your_app.TwitterProfileModel, related_name="tweet_mentions")
    retweeted_status = models.ForeignKey(your_app.TweetModel, related_name="retweets")
    in_reply_to_status = models.ForeignKey(your_app.TweetModel, related_name="replies")
    quoted_status = models.ForeignKey(your_app.TweetModel, related_name="quotes")
    """

    def __str__(self):

        return "{0}, {1}:\nhttps://twitter.com/{2}/status/{3}/:\n {4}".format(
            self.profile,
            self.created_at,
            self.profile.screen_name,
            self.twitter_id,
            decode_text(self.text)
        )

    def update_from_json(self, tweet_data=None, get_retweeted_or_quoted_text=True, is_gnip=False):

        if not tweet_data:
            tweet_data = self.json
        if tweet_data:

            self.created_at = date_parse(tweet_data['created_at'])
            self.retweet_count = tweet_data.get("retweet_count", None)
            self.favorite_count = tweet_data.get("favorite_count", None)
            self.language = tweet_data.get('lang', None)

            #Discovered full_text areas
            #['extended_tweet/full_text/', 'retweeted_status/extended_tweet/full_text/',
            # 'quoted_status/extended_tweet/full_text/,  '
            # retweeted_status / quoted_status / extended_tweet / full_text / ']

            if tweet_data.get('extended_tweet', {}).get('full_text', None):
                full_text = tweet_data.get('extended_tweet', {}).get('full_text', '')
            elif get_retweeted_or_quoted_text:
                if tweet_data.get('retweeted_status', {}).get('extended_tweet', {}).get('full_text', None):
                    full_text = tweet_data.get('retweeted_status', {}).get('extended_tweet', {}).get('full_text', '')
                elif tweet_data.get('quoted_status', {}).get('extended_tweet', {}).get('full_text', None):
                    full_text = tweet_data.get('quoted_status', {}).get('extended_tweet', {}).get('full_text', '')
                elif tweet_data.get('retweeted_status', {}).get(
                        'quoted_status', {}).get('extended_tweet', {}).get('full_text', None):
                    full_text = tweet_data.get('retweeted_status', {}).get(
                        'quoted_status', {}).get('extended_tweet', {}).get('full_text', None)
                else:
                    full_text = None
            else:
                full_text = None

            if full_text: self.text = full_text
            else: self.text = tweet_data.get('text', '')
            self.text = u"{}".format(self.text)

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

            self.json = tweet_data

            try: self.save()
            except:
                try:
                    self.json = decode_text(self.json)
                    self.save()
                except Exception as e:
                    print(e)
                    import pdb
                    pdb.set_trace()
                # \u0000

    def update_relations_from_json(self, tweet_data=None): # TODO: rename

        if not tweet_data:
            tweet_data = self.json
        if tweet_data:

            if not self.pk:
                self.save()
                self.refresh_from_db()

            # PROFILE
            profile_model = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWITTER_PROFILE_MODEL)
            author, created = profile_model.objects.get_or_create(twitter_id=tweet_data['user']['id_str'])
            author.update_from_json(tweet_data['user'])
            self.profile = author

            # USER MENTIONS
            user_mentions = []
            for user_mention in tweet_data.get("entities", {}).get("user_mentions", []):
                existing_profiles = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWITTER_PROFILE_MODEL)\
                    .objects.filter(twitter_id=user_mention["id_str"])
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
                    mentioned_profile, created = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWITTER_PROFILE_MODEL) \
                        .objects.get_or_create(twitter_id=user_mention["id_str"])
                    user_mentions.append(mentioned_profile)
            self.user_mentions = user_mentions

            # HASHTAGS --
            hashtags = []
            for hashtag in tweet_data.get("entities", {}).get("hashtags", []):
                hashtag_obj, created = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWITTER_HASHTAG_MODEL) \
                    .objects.get_or_create(name=hashtag['text'].lower())
                hashtags.append(hashtag_obj)
            self.hashtags = hashtags # [u"{}".format(h) for h in hashtags]

            # REPLY TO STATUS
            if tweet_data.get('in_reply_to_status_id', None):
                tweet_obj, created = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWEET_MODEL) \
                    .objects.get_or_create(twitter_id=tweet_data['in_reply_to_status_id_str'].lower())
                tweet_obj.refresh_from_db()
                if not tweet_obj.profile and tweet_data.get('in_reply_to_user_id_str', None):
                    reply_author_obj, created = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWITTER_PROFILE_MODEL) \
                        .objects.get_or_create(twitter_id=tweet_data['in_reply_to_user_id_str'].lower())
                    tweet_obj.profile = reply_author_obj
                    tweet_obj.save()
                self.in_reply_to_status = tweet_obj

            # QUOTE STATUS
            if tweet_data.get('quoted_status', None):
                tweet_obj, created = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWEET_MODEL) \
                    .objects.get_or_create(twitter_id=tweet_data['quoted_status']['id_str'].lower())
                tweet_obj.update_from_json(tweet_data['quoted_status'])
                tweet_obj.update_relations_from_json(tweet_data['quoted_status'])
                self.quoted_status = tweet_obj

            # RETWEETED STATUS
            if tweet_data.get('retweeted_status', None):
                tweet_obj, created = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWEET_MODEL) \
                    .objects.get_or_create(twitter_id=tweet_data['retweeted_status']['id_str'].lower())
                tweet_obj.update_from_json(tweet_data['retweeted_status'])
                tweet_obj.update_relations_from_json(tweet_data['retweeted_status'])
                self.retweeted_status = tweet_obj

            self.json = tweet_data
            try: self.save()
            except:
                try:
                    self.json = decode_text(self.json)
                    self.save()
                except Exception as e:
                    print(e)
                    import pdb
                    pdb.set_trace()
                # \u0000

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
            self.error = 'No data'
        if score_data:
            self.automation_probability_english = score_data.get('cap', {}).get('english', 0)
            self.automation_probability_universal = score_data.get('cap', {}).get('universal', 0)
            self.content_score = score_data.get('display_scores', {}).get('content', 0)
            self.friend_score = score_data.get('display_scores', {}).get('friend', 0)
            self.network_score = score_data.get('display_scores', {}).get('network', 0)
            self.sentiment_score = score_data.get('display_scores', {}).get('sentiment', 0)
            self.temporal_score = score_data.get('display_scores', {}).get('temporal', 0)
            self.user_score = score_data.get('display_scores', {}).get('user', 0)
            self.overall_score_english = score_data.get('display_scores', {}).get('english', 0)
            self.overall_score_universal = score_data.get('display_scores', {}).get('universal', 0)
            self.json = score_data
            if api_version:
                self.api_version = api_version
            self.save()

class AbstractTwitterRelationship(with_metaclass(AbstractTwitterBase, models.Model)):

    class Meta(object):
        abstract = True


    date = models.DateField(auto_now=True)
    run_id = models.IntegerField(null=True)

    """
    AUTO-CREATED RELATIONSHIPS:
    follower = models.ForeignKey(your_app.TwitterProfileModel, related_name="following_details")
    following = models.ForeignKey(your_app.TwitterProfileModel, related_name="follower_details")
    """

    def __str__(self):
        return "{} following {}".format(self.follower, self.following)


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

