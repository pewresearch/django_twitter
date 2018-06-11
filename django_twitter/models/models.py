from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField
from picklefield.fields import PickledObjectField
from simple_history.models import HistoricalRecords
from dateutil.parser import parse as date_parse
from datetime import datetime

from django_commander.models import LoggedExtendedModel
from pewtils import decode_text, is_not_null, is_null


class AbstractTwitterProfile(BasicExtendedModel):

    twitter_id = models.CharField(max_length=150, db_index=True, help_text="The Twitter account ID")

    tweet_backfilled = models.BooleanField(default=False,
                                         help_text="An indicator used in the sync_tweets management function; True indicates that the user's \
        tweet history has been backfilled as far as possible, so the sync function will stop after it hits an existing \
        tweet the next time it runs.")

    screen_name = models.CharField(max_length=100, db_index=True, null=True, help_text="Twitter screen name")
    description = models.TextField(null=True)
    status = models.TextField(null=True)
    urls = ArrayField(models.CharField(max_length=300), default=[])
    contributors_enabled = models.NullBooleanField(null=True)
    is_verified = models.NullBooleanField(null=True)
    created_at = models.DateTimeField(null=True)
    profile_image_url = models.TextField(null=True)

    location = models.ForeignKey('TwitterPlace', related_name = 'twitter_profiles', null = True)
    language = models.CharField(max_length = 255, null = True) # I DON'T THINK THIS IS NECESSARY
    utc_offset = models.CharField(max_length = 255, null = True) # not sure this needs to be a charfield.
    last_updated = models.DateTimeField(auto_now = True, null = True) # think the tweet_backfill takes care of this

    favorites_count = models.IntegerField(null=True)
    followers_count = models.IntegerField(null=True)
    friends_count = models.IntegerField(null=True)
    listed_count = models.IntegerField(null=True)
    statuses_count = models.IntegerField(null=True)

    lists = models.ForeignKey()

    historical = models.BooleanField(default=False)

    json = JSONField(null=True, default=dict)

    history = HistoricalRecords()

    followers = models.ManyToManyField("django_twitter.TwitterProfile", related_name="friends", through="django_twitter.TwitterFollow",
                                       symmetrical=False)

    ### Removed from this version; were in other ones
    #name = models.CharField(max_length=200, null=True)
    #location = models.TextField(null=True)
    ### Added from Rookery
    #geo_enabled = models.NullBooleanField()
    # We're going to need to see what we need to do to be compliant with the GDPR here
    #location = models.CharField(max_length = 512, null = True) # 256 in Dippybird
    #time_zone = models.CharField(max_length = 255, null = True) # not sure if this will still be in API
    #### Added from Dippybird - I think this can go in another object?
    # profile_inferred_latitude_openstreet = models.FloatField(null=True)
    # profile_inferred_longitude_openstreet = models.FloatField(null=True)
    # profile_inferred_latitude_google = models.FloatField(null=True)
    # profile_inferred_longitude_google = models.FloatField(null=True)
    # profile_inferred_latitude_bing = models.FloatField(null=True)
    # profile_inferred_longitude_bing = models.FloatField(null=True)
    # Let's pull this out
    # botometer_content = models.FloatField(null=True)
    # botometer_friend = models.FloatField(null=True)
    # botometer_network = models.FloatField(null=True)
    # botometer_sentiment = models.FloatField(null=True)
    # botometer_temporal = models.FloatField(null=True)
    # botometer_user = models.FloatField(null=True)
    # botometer_scores_english = models.FloatField(null=True)
    # botometer_scores_universal = models.FloatField(null=True)



    def __str__(self):
        
        return self.screen_name # Can this include some more info? I've in the past included the constructed the URL

    def save(self, *args, **kwargs):

        if self.twitter_id:
            self.twitter_id = str(self.twitter_id).lower()
        self.last_updated = datetime.now()
        super(AbstractTwitterProfile, self).save(*args, **kwargs)

    def update_from_json(self, profile_data=None):

        if not profile_data:
            profile_data = self.json
        if profile_data:
            # TODO: Last step - Verify that all of the fields above are in here
            self.screen_name = profile_data['screen_name'].lower()
            self.created_at = date_parse(profile_data['created_at'])
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


class AbstractTweet(BasicExtendedModel):

    profile = models.ForeignKey("django_twitter.TwitterProfile", related_name="tweets", help_text="The parent Twitter profile")
    twitter_id = models.CharField(max_length=200, db_index=True, unique=True, help_text="Uses the unique identifier provided \
        by Twitter")

    # Rookery calls this created_at - I think that would be good for consistency
    created_at = models.DateTimeField(null=True, help_text="The time/date that the tweet was published")
    links = ArrayField(models.CharField(max_length=400), default=[], null=True,
                       help_text="Links contained in the tweet")

    # Added from Rookery
    place = models.ForeignKey('TwitterPlace', related_name = 'tweets', null = True)
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

    user_mentions = models.ManyToManyField("AbstractTwitterProfile", related_name="tweet_mentions")
    hashtags = models.ManyToManyField("AbstractTwitterHashtag", related_name="tweets")

    json = PickledObjectField(null=True)

    last_update_time = models.DateTimeField(auto_now=True, null=True,
                                            help_text="The last time the tweet was updated from the API"
                                            )

    history = HistoricalRecords()

    def __str__(self):

        return "{0}, {1}: {2}".format(
            self.profile,
            self.timestamp,
            decode_text(self.document.text) if self.document and self.document.text else None # I don't understand this business
        )

    def save(self, *args, **kwargs):

        if self.twitter_id:
            self.twitter_id = str(self.twitter_id).lower()
        super(AbstractTweet, self).save(*args, **kwargs)

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

# class Link(BasicExtendedModel):
#
#     tw_display_url = models.CharField(max_length=140, null=True, db_index=True)
#     tw_expanded_url = models.CharField(max_length=1000, null=True, db_index=True)
#     tw_expanded_url_title = models.CharField(max_length=250, null=True)
#     tw_expanded_url_description = models.TextField(null=True)
#
#     expanded_url = models.CharField(max_length=1000, null=True, db_index=True)
#
#     domain = models.ForeignKey('dippybird.Domain', related_name='links', null=True, on_delete=models.SET_NULL)
#
#     last_expand_time = models.DateTimeField(blank=True, null=True)
#     last_domain_extract_time = models.DateTimeField(blank=True, null=True)
#
#     class Meta:
#         unique_together = ("tw_display_url", "tw_expanded_url")
#
#     def __str__(self):
#
#         if self.expanded_url: url =  self.expanded_url
#         elif self.tw_expanded_url: url = self.tw_expanded_url
#         else: url = self.tw_display_url
#
#         if len(url) >= 75: return "{}...".format(url[:75])
#         else: return url
#
#     def save(self, *args, **kwargs):
#         if self.tw_expanded_url_title and len(self.tw_expanded_url_title) > 250:
#             new_desc = self.tw_expanded_url_title
#             if self.tw_expanded_url_description:
#                 new_desc = new_desc + u"\n" + self.tw_expanded_url_description
#             self.tw_expanded_url_description = new_desc
#             self.tw_expanded_url_title = self.tw_expanded_url_title[:200]
#
#         super(Link, self).save(*args, **kwargs)
#
#     def expand_url(self, refresh=False, override_url=None, reextract_domain=False):
#
#         # url_shorteners = ["bit.ly","dld.bz","fb.me", "youtu.be"]
#
#         original = self.expanded_url
#         if override_url:
#             try:
#                 self.expanded_url = override_url
#                 self.last_expand_time = timezone.now()
#                 self.save()
#             except django.db.utils.DataError:
#                 self.expanded_url = None
#                 self.last_expand_time = timezone.now()
#                 self.save()
#         elif not self.expanded_url or refresh:
#             try:
#                 url_to_expand = self.tw_expanded_url if self.tw_expanded_url else self.tw_display_url
#                 self.expanded_url = canonical_link(url_to_expand, timeout=5, full_resolve=True)
#                 self.last_expand_time = timezone.now()
#                 self.save()
#             except django.db.utils.DataError:
#                 self.expanded_url = None
#                 self.last_expand_time = timezone.now()
#                 self.save()
#             except Exception as e:
#                 print(e)
#         if self.expanded_url != original or reextract_domain:
#             self.extract_domain(refresh=True)
#
#     def extract_domain(self, refresh=False):
#
#         if not self.domain or refresh:
#             self.domain = None
#             exp_url = self.expanded_url
#             if not exp_url: exp_url = self.tw_expanded_url
#             if exp_url:
#                 temp_domain = extract_domain_from_url(exp_url, include_subdomain=False)
#                 if temp_domain:
#                     # parsed_url = urlsplit(self.expanded_url)
#                     # temp_domain = parsed_url.netloc
#                     # if temp_domain.startswith('www.'):
#                     #     temp_domain = temp_domain[4:]
#                     try: domain, created = Domain.objects.get_or_create(name=temp_domain)
#                     except django.db.utils.DataError: domain = None
#                     self.domain = domain
#                 else:
#                     self.domain = None
#             self.last_domain_extract_time = timezone.now()
#             self.save()
#
# # Not sure if this should go in here - it's definitely a different idea - maybe a centralized link/domain object?
# # It just feels weird to put this in the Twitter object
#
# class Domain(BasicExtendedModel):
#
#     DOMAIN_CATEGORIES = (
#         ("news", "News/Political/Opinion"),
#         ("entertain", "Entertainment/Media/Art"),
#         ("tech", "Tech News"),
#         ("social", "Social/Sharing"),
#         ("sports", "Sports"),
#         ("business", "Business/Finance"),
#         ("ecommerce", "eCommerce/Shopping/Retail"),
#         ("activism", "Activism/Causes/Petitions"),
#         ("links", "Link Shorteners"),
#         ("viral", "Clickbait/Viral"),
#         ("spam", "Spam/Advertising Garbage"),
#         ("misc", "Miscellaneous"),
#         ("unk", "Unknown")
#     )
#
#     name = models.CharField(max_length=100, unique=True)
#     category = models.CharField(max_length=150, choices=DOMAIN_CATEGORIES, null=True, blank=True)
#     reputable = models.BooleanField(default=True)
#     use_botometer = models.BooleanField(default=False)
#
#     def __str__(self):
#         return self.name


class AbstractTwitterRelationship(BasicExtendedModel): # Recommend rename to relationship?
    
    friend = models.ForeignKey("django_twitter.TwitterProfile", related_name="follower_details")
    follower = models.ForeignKey("django_twitter.TwitterProfile", related_name="friend_details")
    dates = ArrayField(models.DateField(), default=[])

    class Meta:
        unique_together = ("friend", "follower")

    def __str__(self):
        return "{} following {}".format(self.follower, self.friend)


class AbstractTwitterHashtag(BasicExtendedModel):
    name = models.CharField(max_length=150, unique=True, db_index=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        super(AbstractTwitterHashtag, self).save(*args, **kwargs)

####
class AbstractTwitterPlace(BasicExtendedModel):

    place_id = models.CharField(max_length = 255, db_index = True, unique = True)
    full_name = models.CharField(max_length = 255)
    place_type = models.CharField(max_length = 255)
    country_code = models.CharField(max_length = 10)
    country = models.CharField(max_length = 255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True)

# class TwitterLink(models.Model):
#     class Meta:
#         app_label = 'rookery_journalism'
#
#     full            = models.CharField(max_length = 4096, db_index = True, unique = True)
#     tweets          = models.ManyToManyField('TwitterTweet', related_name = 'links')
#     scheme          = models.CharField(max_length = 10, null = True)
#     username        = models.CharField(max_length = 255, null = True)
#     password        = models.CharField(max_length = 255, null = True)
#     hostname        = models.CharField(max_length = 255, null = True)
#     port            = models.CharField(max_length = 5, null = True)
#     path            = models.CharField(max_length = 1024, null = True)
#     query           = models.CharField(max_length = 512, null = True)
#     last_updated    = models.DateTimeField(auto_now = True)
#     history         = HistoricalRecords()
#     objects         = TwitterLinkManager()
#
#     def save(self, *args, **kwargs):
#         splitLink = urlsplit(self.full)
#
#         for attr in ['scheme', 'username', 'password', 'hostname', 'port', 'path', 'query']:
#             a = getattr(splitLink, attr, None)
#             if a: setattr(self, attr, a)
#
#         super(TwitterLink, self).save(*args, **kwargs)

#######
# These are in Rookery but probably arent' needed in the broader apihooks
# class TwitterSearch(models.Model):
#     class Meta:
#         app_label = 'rookery_journalism'
#
#     name            = models.CharField(max_length = 255, db_index = True, unique = True)
#     query           = models.CharField(max_length = 1024)
#     tweets          = models.ManyToManyField('TwitterTweet', related_name = 'searches')
#     last_updated    = models.DateTimeField(auto_now = True)
#     history         = HistoricalRecords()
#     objects         = TwitterSearchManager()

class TwitterList(BasicExtendedModel):

    list_id = models.CharField(max_length = 255, db_index = True, unique = True)
    name = models.CharField(max_length = 255, null = True)
    owner = models.ForeignKey('AbstractTwitterProfile', related_name = 'lists_created')
    members = models.ManyToManyField('TwitterUser', related_name = 'lists_on')
    tweets = models.ManyToManyField('TwitterTweet', related_name = 'lists_on')
    slug = models.SlugField(max_length = 255, null = True)
    member_count = models.IntegerField(null = True)

    last_updated = models.DateTimeField(auto_now = True)
    history = HistoricalRecords()
    # objects             = TwitterListManager()

#####
# These are from Dippybird
# I think we could include Location, but not KeywordQuery or RegExMatch
class Location(BasicExtendedModel):

    tw_id = models.CharField(max_length=50, unique=True)
    place_type = models.CharField(max_length=50)
    country = models.CharField(max_length=50)
    name = models.CharField(max_length=256)
    full_name = models.CharField(max_length=256)

    json = PickledObjectField(null=True)

    def save(self, *args, **kwargs):

        if not all([self.name, self.place_type] or kwargs.get("reparse", False)):
            self.place_type = self.json["place_type"]
            self.country = self.json["country"]
            self.name = self.json["name"]
            self.full_name = self.json["full_name"]
        super(Location, self).save(*args, **kwargs)


# class KeywordQuery(BasicExtendedModel):
#
#     name = models.CharField(max_length=100, db_index=True, unique=True)
#     query = ArrayField(models.TextField(), default=[])
#
#     def __str__(self):
#         return self.name
#
#
# class RegexMatch(BasicExtendedModel):
#
#     name = models.CharField(max_length=100, db_index=True, unique=True)
#     regex = models.CharField(max_length=2000, null=True)
#
#     def __str__(self):
#         return self.name