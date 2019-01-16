# from __future__ import unicode_literals
# from django.db import models
# from simple_history.models import HistoricalRecords
# from django.contrib.postgres.fields import JSONField
# from urlparse import urlsplit
#
# class TwitterUserManager(models.Manager):
#     pass
#
#
# class TwitterUser(models.Model):
#     class Meta:
#         app_label = 'rookery_journalism'
#
#     user_id                 = models.CharField(max_length = 255, db_index = True, unique = True)
#     contributors_enabled    = models.NullBooleanField()
#     created_at              = models.DateTimeField(null = True)
#     description             = models.CharField(max_length = 512, null = True)
#     favorites_count         = models.IntegerField(null = True)
#     followers_count         = models.IntegerField(null = True)
#     friends_count           = models.IntegerField(null = True)
#     geo_enabled             = models.NullBooleanField()
#     lang                    = models.CharField(max_length = 255, null = True)
#     listed_count            = models.IntegerField(null = True)
#     location                = models.CharField(max_length = 512, null = True)
#     name                    = models.CharField(max_length = 255, null = True)
#     screen_name             = models.CharField(max_length = 255, null = True)
#     statuses_count          = models.IntegerField(null = True)
#     time_zone               = models.CharField(max_length = 255, null = True)
#     utc_offset              = models.CharField(max_length = 255, null = True)
#     url                     = models.CharField(max_length = 255, null = True)
#     verified                = models.NullBooleanField()
#     last_updated            = models.DateTimeField(auto_now = True, null = True)
#     history                 = HistoricalRecords()
#     objects                 = TwitterUserManager()
#
#
# class TwitterTweetManager(models.Manager):
#     pass
#
#
# class TwitterTweet(models.Model):
#     class Meta:
#         app_label = 'rookery_journalism'
#
#     tweet_id                = models.CharField(max_length = 255, db_index = True, unique = True)
#     user                    = models.ForeignKey('TwitterUser', related_name = 'tweets')
#     place                   = models.ForeignKey('TwitterPlace', related_name = 'tweets', null = True)
#     created_at              = models.DateTimeField(null = True)
#     favorite_count          = models.IntegerField(null = True)
#     in_reply_to_screen_name = models.CharField(max_length = 255, null = True)
#     in_reply_to_status_id   = models.CharField(max_length = 255, null = True)
#     in_reply_to_user_id     = models.CharField(max_length = 255, null = True)
#     lang                    = models.CharField(max_length = 255, null = True)
#     latitude                = models.DecimalField(max_digits = 9, decimal_places = 6, null = True)
#     longitude               = models.DecimalField(max_digits = 9, decimal_places = 6, null = True)
#     retweet_count           = models.IntegerField(null = True)
#     quoted_status_id        = models.CharField(max_length = 255, null = True)
#     source                  = models.CharField(max_length = 255, null = True)
#     text                    = models.CharField(max_length = 1024, null = True)
#     last_updated            = models.DateTimeField(auto_now = True)
#     history                 = HistoricalRecords()
#     objects                 = TwitterTweetManager()
#
#
# class TwitterListManager(models.Manager):
#     pass
#
#
# class TwitterList(models.Model):
#     class Meta:
#         app_label = 'rookery_journalism'
#
#     list_id             = models.CharField(max_length = 255, db_index = True, unique = True)
#     owner               = models.ForeignKey('TwitterUser')
#     members             = models.ManyToManyField('TwitterUser', related_name = 'lists')
#     tweets              = models.ManyToManyField('TwitterTweet', related_name = 'lists')
#     name                = models.CharField(max_length = 255, null = True)
#     slug                = models.SlugField(max_length = 255, null = True)
#     member_count        = models.IntegerField(null = True)
#     last_updated        = models.DateTimeField(auto_now = True)
#     history             = HistoricalRecords()
#     objects             = TwitterListManager()
#
#
# class TwitterSearchManager(models.Manager):
#     pass
#
#
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
#
#
# class TwitterPlaceManager(models.Manager):
#     pass
#
#
# class TwitterPlace(models.Model):
#     class Meta:
#         app_label = 'rookery_journalism'
#
#     place_id        = models.CharField(max_length = 255, db_index = True, unique = True)
#     full_name       = models.CharField(max_length = 255)
#     place_type      = models.CharField(max_length = 255)
#     country_code    = models.CharField(max_length = 10)
#     country         = models.CharField(max_length = 255)
#
#
# class TwitterLinkManager(models.Manager):
#     pass
#
#
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
