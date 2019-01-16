# import requests, time, django, re
# import json
# from urlparse import urlparse
#
# from django.core.files.base import ContentFile
# from datetime import datetime
# from urlparse import urlsplit, urlparse
# from django.db import models
# from django.utils import timezone
# from django.conf import settings
# from django.contrib.postgres.fields import ArrayField
# from picklefield.fields import PickledObjectField
# from dateutil.parser import parse as parse_date
#
# from pewtils.django.abstract_models import BasicExtendedModel
# from pewtils.http import canonical_link, extract_domain_from_url
# from pewtils import decode_text, is_not_null
# from pewtils.django import consolidate_objects
#
# from dippybird.utils import RT_MATCH_REGEX, check_if_list_has_text
#
#
# class TwitterUser(BasicExtendedModel):
#
#     user_id = models.CharField(max_length=25, null=True, db_index=True, unique=True)
#     screen_name = models.CharField(max_length=15, null=True, db_index=True)
#     created_at = models.DateTimeField(null=True)
#     has_default_profile = models.NullBooleanField(null=True)
#     has_default_profile_image = models.NullBooleanField(null=True)
#     favorites_count = models.IntegerField(null=True)
#     follower_count = models.IntegerField(null=True)
#     friend_count = models.IntegerField(null=True)
#     listed_count = models.IntegerField(null=True)
#     status_count = models.IntegerField(null=True)
#
#     location = models.CharField(max_length=256, null=True)
#     profile_inferred_latitude_openstreet = models.FloatField(null=True)
#     profile_inferred_longitude_openstreet = models.FloatField(null=True)
#     profile_inferred_latitude_google = models.FloatField(null=True)
#     profile_inferred_longitude_google = models.FloatField(null=True)
#     profile_inferred_latitude_bing = models.FloatField(null=True)
#     profile_inferred_longitude_bing = models.FloatField(null=True)
#
#     json = PickledObjectField(null=True)
#     #json = models.FileField(upload_to="twitter_users", null=True, blank=True)
#
#     # New fields - added by Stefan
#     botometer_checked = models.BooleanField(default=False)
#     botometer_content = models.FloatField(null=True)
#     botometer_friend = models.FloatField(null=True)
#     botometer_network = models.FloatField(null=True)
#     botometer_sentiment = models.FloatField(null=True)
#     botometer_temporal = models.FloatField(null=True)
#     botometer_user = models.FloatField(null=True)
#     botometer_scores_english = models.FloatField(null=True)
#     botometer_scores_universal = models.FloatField(null=True)
#     #######
#
#     def __str__(self):
#         return "{}:{}".format(self.user_id, self.screen_name)
#
#
#     def save(self, *args, **kwargs):
#         if not all([self.screen_name, self.user_id]) or kwargs.get("reparse", False):
#             try:
#                 self.user_id = self.json["id_str"]
#             except KeyError:
#                 # This means it's from GNIP and not Twitter API
#                 self.user_id = self.json["id"].split(':')[-1]
#                 self.screen_name = self.json["preferredUsername"]
#                 self.created_at = parse_date(self.json["postedTime"])
#                 self.favorites_count = self.json["favoritesCount"]
#                 self.friend_count = self.json["friendsCount"]
#                 self.follower_count = self.json["followersCount"]
#                 self.status_count = self.json["statusesCount"]
#             else:
#                 self.screen_name = self.json["screen_name"]
#                 self.created_at = parse_date(self.json["created_at"])
#                 self.has_default_profile = self.json["default_profile"]
#                 self.has_default_profile_image = self.json["default_profile_image"]
#                 self.favorites_count = self.json["favourites_count"]
#                 self.follower_count = self.json["followers_count"]
#                 self.friend_count = self.json["friends_count"]
#                 self.listed_count = self.json["listed_count"]
#                 self.status_count = self.json["statuses_count"]
#                 self.location = self.json.get("location", None)
#
#         super(TwitterUser, self).save(*args, **kwargs)
#
#
# class Location(BasicExtendedModel):
#
#     tw_id = models.CharField(max_length=50, unique=True)
#     place_type = models.CharField(max_length=50)
#     country = models.CharField(max_length=50)
#     name = models.CharField(max_length=256)
#     full_name = models.CharField(max_length=256)
#
#     json = PickledObjectField(null=True)
#
#     def save(self, *args, **kwargs):
#
#         if not all([self.name, self.place_type] or kwargs.get("reparse", False)):
#             self.place_type = self.json["place_type"]
#             self.country = self.json["country"]
#             self.name = self.json["name"]
#             self.full_name = self.json["full_name"]
#         super(Location, self).save(*args, **kwargs)
#
#
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
#
# class Tweet(BasicExtendedModel):
#
#     tw_id = models.CharField(max_length=20, default='', unique=True) # From Twitter
#
#     user = models.ForeignKey("dippybird.TwitterUser", related_name="tweets", null=True)
#     date_posted = models.DateTimeField(blank=True, null=True)
#     date_collected = models.DateTimeField(auto_now_add=True)
#     links = models.ManyToManyField("dippybird.Link", related_name="tweets")
#     text = models.TextField(null=True)
#     regex_text = models.TextField(null=True)
#
#     retweeted = models.NullBooleanField(null=True)
#     retweet_count = models.IntegerField(null=True)
#     favorited = models.NullBooleanField(null=True)
#     favorite_count = models.IntegerField(null=True)
#     possibly_sensitive = models.NullBooleanField(null=True)
#     is_reply = models.NullBooleanField(null=True)
#
#     latitude = models.FloatField(null=True)
#     longitude = models.FloatField(null=True)
#     location = models.ForeignKey("dippybird.Location", related_name="tweets", null=True)
#
#     keyword_queries = models.ManyToManyField("dippybird.KeywordQuery", related_name="tweets")
#     regex_matches = models.ManyToManyField("dippybird.RegexMatch", related_name="tweets")
#
#     json = PickledObjectField(null=True)
#
#     gnip = models.BooleanField(default=False)
#     batch_id = models.IntegerField(default=None, null=True)
#
#     last_link_extract_time = models.DateTimeField(blank=True, null=True)
#     last_text_extract_time = models.DateTimeField(blank=True, null=True)
#
#     #json = models.FileField(upload_to="tweets", null=True, blank=True)
#
#     def __str__(self):
#
#         # ran into a bug in which it tries to return this before a save.
#         try:
#             return "twitter.com/{}/status/{}".format(self.user.screen_name, self.tw_id)
#         except:
#             return self.tw_id
#
#     def save(self, *args, **kwargs):
#
#         if not hasattr(self, "user") or (not all([self.user, self.date_posted]) or kwargs.get("reparse", False)):
#
#             if self.gnip:
#
#                 self.user = TwitterUser.objects.create_or_update(
#                     {"user_id": self.json["actor"]["id"].split(':')[-1]},
#                     {"json":self.json["actor"]}
#                 )
#                 self.date_posted = parse_date(self.json["postedTime"])
#
#                 if self.json.get('retweetCount', {}):
#                     self.retweet_count = self.json['retweetCount']
#                 else:
#                     self.retweet_count = 0
#                 self.retweeted = (self.retweet_count > 0)
#
#                 if self.json.get('favoritesCount'):
#                     self.favorite_count = self.json['favoritesCount']
#                 self.favorited = (self.favorite_count > 0)
#
#                 self.possibly_sensitive = False # no values for this in gnip
#                 self.is_reply = True if any(self.json.get('inReplyTo','')) else False
#
#                 # and no geolcation info is kept in gnip, so not worrying about that
#
#             else:
#
#                 self.user = TwitterUser.objects.create_or_update(
#                     {"user_id": self.json["user"]["id"]},
#                     {"json": self.json["user"]}
#                 )
#                 self.date_posted = parse_date(self.json["created_at"])
#                 self.retweeted = self.json["retweeted"]
#                 self.retweet_count = self.json["retweet_count"]
#                 self.favorited = self.json["favorited"]
#                 self.favorite_count = self.json["favorite_count"]
#                 self.possibly_sensitive = self.json.get("possibly_sensitive", None)
#                 self.is_reply = True if any([
#                     self.json["in_reply_to_screen_name"],
#                     self.json["in_reply_to_status_id"],
#                     self.json["in_reply_to_user_id"]
#                 ]) else False
#                 if self.json.get('geo', None) and self.json['geo'].get("type", None) == "Point":
#                     self.latitude = self.json['geo']['coordinates'][0]
#                     self.longitude = self.json['geo']['coordinates'][1]
#                 if self.json.get("place", None):
#                     self.location = Location.objects.create_or_update(
#                         {"tw_id": self.json["place"]["id"]},
#                         {"json": self.json["place"]}
#                     )
#
#         super(Tweet, self).save(*args, **kwargs)
#
#     def extract_text(self, include_links=False):
#
#         if self.gnip:
#             text = self._get_tweet_text_gnip()
#         else:
#             text = self._get_tweet_text_twitterapi()
#         self.text = text
#
#         if include_links:
#             for link in self.links.all():
#                 # don't want to include retweet info because that may include usernames
#                 if link.tw_expanded_url and "twitter.com" not in link.tw_expanded_url:
#                     try:
#                         temp_text = u"\n{}\n{}\n{}".format(link.expanded_url,
#                                                            link.tw_expanded_url_title,
#                                                            link.tw_expanded_url_description)
#                     except:
#                         try:
#                             temp_text += u"\n{}\n{}\n{}".format(decode_text(link.expanded_url),
#                                                                 decode_text(link.tw_expanded_url_title),
#                                                                 decode_text(link.tw_expanded_url_description))
#                         except:
#                             temp_text = ''
#                     text += temp_text
#
#         self.regex_text = text
#         self.last_text_extract_time = timezone.now()
#         self.save()
#
#     def _get_tweet_text_twitterapi(self, strip_retweet=True):
#         '''
#         Combines the current tweet text with the text of any retweet or quoted tweet.
#         Also excludes the RT @username if current tweet is just a retweet.
#         Does not include any links or their descriptions.
#         :param tweet: full tweet json object
#         :param strip_retweet: Boolean to strip the RT @username language. Default true
#         :return: text as shown on the
#         '''
#         retweeted_text = ''
#         quoted_text = ''
#
#         tweet_payload = self.json
#
#         # first, get text from tweet
#         tweet_text = self._get_text_from_object_twitterapi(tweet_payload)
#
#         # Is it a retweet?
#         # The retweeted text will just be "RT @username: <text>"
#         # So we'll want to replace the text with that
#         if tweet_payload.get('retweeted_status', None):
#             # sometimes text is full_text, sometimes text
#             retweeted_text = self._get_text_from_object_twitterapi(tweet_payload['retweeted_status'])
#
#             # check if the current text is just a retweet. If so, set text to that
#             # otherwise, add retweeted text
#             curr_tweet_text_match = RT_MATCH_REGEX.match(tweet_text)
#             if curr_tweet_text_match:
#                 if retweeted_text.startswith(curr_tweet_text_match.groups()[0][:-5]):
#                     if strip_retweet:
#                         tweet_text = retweeted_text
#                     retweeted_text = ''
#
#         # and finally check for quoted_status
#         if tweet_payload.get('quoted_status', None):
#             quoted_text = self.get_text_from_object_twitterapi(tweet_payload['quoted_status'])
#
#         # and compile
#         final_text = u"{}\n{}\n{}".format(tweet_text, retweeted_text, quoted_text)
#
#         # and return
#         return final_text
#
#     def _get_text_from_object_twitterapi(self, payload_object):
#         '''
#         Pulls the text from a tweet object, which may be in the full_text field or the text field
#         :param payload_object: tweet object in json. Could be a tweet, retweeted_status, or quoted_status object
#         :return: full text of tweet
#         '''
#         # may be in the full_text (seems to occur with replies)
#         # may instead be in the text field
#         if payload_object.get('extended_tweet', {}).get('full_text', None):
#             text = payload_object['extended_tweet']['full_text']
#         else:
#             if payload_object.get('long_object', {}).get("body", None):
#                 text = u"{}".format(payload_object['long_object']['body'])
#             elif payload_object.get('body', None): # TODO: it's good practice to use Nones instead of an empty string, if it's just needed for a conditional
#                 text = payload_object['body']
#             else:
#                 text = payload_object.get('text', '')
#         return text
#
#     def _get_tweet_text_gnip(self, strip_retweet=True):
#         '''
#         Returns full text as it would appear on the screen, including any links and descriptions
#         :param tweet_payload: JSON of tweet from GNIP
#         :return: full text, including links
#         '''
#         tweet_payload = self.json
#
#         tweet_text = self._get_text_from_object_gnip(tweet_payload)
#
#         # check if the current text is just a retweet. If so, set text to that
#         # otherwise, add retweeted text
#         curr_tweet_text_match = RT_MATCH_REGEX.match(tweet_text)
#         if curr_tweet_text_match:
#             if strip_retweet:
#                 tweet_text = curr_tweet_text_match.groups()[0]
#                 # TODO: this logic seems slightly different than the twitter api stuff
#                 # TODO: the latter adds RT text to the original tweet text if it's not just a retweet
#                 # TODO: here, it looks like you're just replacing everything with just the RT text
#                 # TODO: shouldn't you be getting the RT text somewhere and adding it to tweet_text like the quoted status below?
#
#         # extract text from a quoted tweet
#         if tweet_payload.get('twitter_quoted_status'):
#             tweet_text += u"\n{}".format(self._get_text_from_object_gnip(tweet_payload['twitter_quoted_status']))
#
#         return tweet_text
#
#     def _get_text_from_object_gnip(self, payload_object):
#         '''
#         Pulls the text from a tweet object, which may be in the full_text field or the text field
#         :param payload_object: tweet object in json. Could be a tweet, retweeted_status, or quoted_status object
#         :return: full text of tweet
#         '''
#         text = u"{}".format(payload_object['body'])
#         curr_tweet_text_match = RT_MATCH_REGEX.match(text)
#         if curr_tweet_text_match and payload_object.get('object', {}).get('body', ''):
#             text = u"{}".format(payload_object['object']['body'])
#
#         # Now check if there's a longer version and if so automatically add that
#         if payload_object['object'].get('long_object', {}).get("body", None): # TODO: expanded these so we don't assume that the long_object always has a 'body' attribute
#             # TODO: best to not make assumptions :P (an even better practice would be to add a conditional to throw a breakpoint in here if it doesnt, but for now we'll silently skip it)
#             # still checking retweet here
#             text = u"{}".format(payload_object['object']['long_object']['body'])
#
#         if payload_object.get('long_object', {}).get("body", None):
#             text = u"{}".format(payload_object['long_object']['body'])
#
#         return text
#
#     def extract_links(self, extract_secondary_links=False, save=False, refresh=False, process=False):
#
#         if self.gnip:
#             links = self._extract_links_gnip(extract_secondary_links=extract_secondary_links)
#         else:
#             links = self._extract_links_twitterapi(extract_secondary_links=extract_secondary_links)
#         if process:
#             for l in links:
#                 l.expand_url(refresh=refresh)
#         if save:
#             self.links = []
#             for l in links:
#                 self.links.add(l)
#             self.last_link_extract_time = timezone.now()
#             self.save()
#         else:
#             return links
#
#
#     def _extract_links_twitterapi(self, extract_secondary_links=False):
#
#         tweet_payload = self.json
#
#         urls = tweet_payload.get("entities", {}).get("urls", [])
#         if "extended_tweet" in tweet_payload.keys():
#             urls += tweet_payload["extended_tweet"].get("entities", {}).get("urls", [])
#
#         subtweets = {'retweeted_status': {}, 'quoted_status': {}}
#         secondary_urls = []
#
#         for subtweet in subtweets.keys():
#             if tweet_payload.get(subtweet, None):
#                 # get original tweet author / id
#                 subtweets[subtweet]['user'] = tweet_payload[subtweet]['user']['screen_name']
#
#                 subtweets[subtweet]['id'] = tweet_payload[subtweet]['id_str']
#                 subtweets[subtweet]['url'] = 'twitter.com/{}/status/{}'.format(
#                                                 subtweets[subtweet]['user'],
#                                                 subtweets[subtweet]['id'])
#                 secondary_urls.append({
#                     'display_url': subtweets[subtweet]['url'],
#                     'expanded_url': subtweets[subtweet]['url']
#                 })
#
#                 secondary_urls.extend(tweet_payload[subtweet].get('entities', {}).get('urls', []))
#
#                 if "extended_tweet" in tweet_payload[subtweet].keys():
#                     secondary_urls += tweet_payload[subtweet].get('extended_tweet', {}).get('entities', {}).get('urls', [])
#
#         links = self._create_link_objects(subtweets, urls, secondary_urls, extract_secondary_links=extract_secondary_links)
#
#         return links
#
#
#     def _extract_links_gnip(self, extract_secondary_links=False):
#
#         '''
#                 Retrieves the links from a gnip json of a tweet.
#                 :param tweet_payload: Json from GNIP
#                 :return: list of links
#                 '''
#
#         tweet_payload = self.json
#
#         # GNIP helpfully adds all links to other tweets (e.g. retweets or quoted tweets)
#         # in the gnip object.
#         # If it is a twitter link, it likely will not be expanded.
#
#         # in some cases, however, there will not be a link at all.
#
#         urls = []
#         if tweet_payload.get('gnip', {}).get('urls', []):
#             urls += tweet_payload['gnip']['urls']
#         if tweet_payload.get('twitter_entities', {}).get('urls', []):
#             urls += tweet_payload['twitter_entities']['urls']
#
#         subtweets = {}
#         secondary_urls = []
#
#         # retweet OR current object
#         if tweet_payload.get('object', {}).get('id', '') and not tweet_payload['object']['link'] == tweet_payload['link']:
#             subtweets['retweet'], temp_secondary_links = self._get_gnip_subtweet_info(tweet_payload['object'], expand_subtweet_urls=(not extract_secondary_links))
#             secondary_urls.extend(temp_secondary_links)
#
#         # quoted tweet
#         if tweet_payload.get('twitter_quoted_status', {}).get('link', None):
#             subtweets['quoted_tweet'], temp_secondary_links = self._get_gnip_subtweet_info(tweet_payload['twitter_quoted_status'], expand_subtweet_urls=(not extract_secondary_links))
#             secondary_urls.extend(temp_secondary_links)
#
#         # retweet with a quoted tweet (doesn't always come through it seems)
#         if tweet_payload.get('object', {}).get('twitter_quoted_status', {}).get('link', None):
#             subtweets['retweet_quoted_tweet'], temp_secondary_links = self._get_gnip_subtweet_info(tweet_payload['object']['twitter_quoted_status'], expand_subtweet_urls=(not extract_secondary_links))
#             secondary_urls.extend(temp_secondary_links)
#
#         links = self._create_link_objects(subtweets, urls, secondary_urls, extract_secondary_links=extract_secondary_links)
#
#         return links
#
#
#     def _get_gnip_subtweet_info(self, subtweet_payload, expand_subtweet_urls=False):
#
#         subtweet = {}
#         subtweet['user'] = subtweet_payload.get('actor', {}).get('displayName', None)
#         subtweet['id'] = subtweet_payload.get('id', '').split(':')[2]
#         if subtweet['id'] == '': subtweet['id'] = None
#         subtweet['url'] = self._format_link(subtweet_payload.get('link', None))
#
#         secondary_links = []
#         secondary_links.append({
#             'display_url': subtweet['url'],
#             'expanded_url': subtweet['url'],
#             'title': None,
#             'description': None
#         })
#         temp_urls = []
#         if subtweet_payload.get('twitter_entities', {}).get('urls', []):
#             temp_urls += subtweet_payload['twitter_entities']['urls']
#         if subtweet_payload.get('long_object', {}).get('twitter_entities', {}).get('urls', []):
#             temp_urls += subtweet_payload['long_object']['twitter_entities']['urls']
#         for url in temp_urls:
#             original_expanded_url = None
#             if url.get('display_url', None):
#                 display_url = self._format_link(url['display_url'])
#             else:
#                 display_url = self._format_link(url['url'])
#             expanded_url = self._format_link(url.get('expanded_url', None))
#             if expand_subtweet_urls and not unicode(expanded_url).startswith(u"twitter.com") and not unicode(display_url).startswith(u"twitter.com"):
#                 original_expanded_url = expanded_url
#                 expanded_url = canonical_link(expanded_url, timeout=5, full_resolve=True)
#                 # in some cases, the expanded subtweet link will make its way into the primary object
#                 # and only the shortened version will be in the secondary subtweet url field
#                 # if we want to skip secondary urls, then it's important that we recognize that the expanded version
#                 # in the main object is removed, even if only the shortened version exists in the subtweet
#             secondary_links.append({
#                 'display_url': display_url,
#                 'expanded_url': expanded_url,
#                 'original_expanded_url': original_expanded_url,
#                 'title': url.get('expanded_url_title', None),
#                 'description': url.get('expanded_url_description', None)
#             })
#
#         return subtweet, secondary_links
#
#
#     def _create_link_objects(self, subtweets, urls, secondary_urls, extract_secondary_links=False):
#
#         # format the link to remove http(s)://www.
#         for url in urls:
#             if url.get('display_url', None):
#                 url['display_url'] = self._format_link(url.get('display_url', None))
#             else:
#                 url['display_url'] = self._format_link(url.get('url', None))
#             url['expanded_url'] = self._format_link(url.get('expanded_url', None))
#             url['original_expanded_url'] = self._format_link(url.get('original_expanded_url', None))
#
#         for url in secondary_urls:
#             if url.get('display_url', None):
#                 url['display_url'] = self._format_link(url['display_url'])
#             else:
#                 url['display_url'] = self._format_link(url['url'])
#             url['expanded_url'] = self._format_link(url.get('expanded_url', None))
#             url['original_expanded_url'] = self._format_link(url.get('original_expanded_url', None))
#
#         all_secondary_urls = []
#         all_secondary_ids = []
#         for subtweet in subtweets.keys():
#             if subtweets[subtweet].get('id', None):
#                 all_secondary_urls.append(subtweets[subtweet]['url'])
#                 all_secondary_ids.append(subtweets[subtweet]['id'])
#         if extract_secondary_links:
#             urls += secondary_urls
#         for url in secondary_urls:
#             display_url = url.get('display_url', None)
#             if display_url: all_secondary_urls.append(display_url)
#             expanded_url = url.get('expanded_url', None)
#             if expanded_url: all_secondary_urls.append(expanded_url)
#             original_expanded_url = url.get('original_expanded_url', None)
#             if original_expanded_url: all_secondary_urls.append(original_expanded_url)
#
#         links = []
#         added_statuses = []
#
#         good_urls = []
#         wonky_urls = []
#         for url in urls:
#             display_url = url.get('display_url', None)
#             expanded_url = url.get('expanded_url', None)
#             if check_if_list_has_text('i/web/status', [display_url, expanded_url]):
#                 wonky_urls.append(url)
#             else:
#                 good_urls.append(url)
#         urls = good_urls + wonky_urls
#         # we only ever want to add the "i/web/status" links if the proper one doesn't exist, so we check other links first
#
#         for url in urls:
#
#             # Only do if the link is not to this user (sometimes that occurs for some reason)
#
#             display_url = url.get("display_url", None)
#             expanded_url = url.get("expanded_url", None)
#             original_expanded_url = url.get("original_expanded_url", None)
#             title = url.get("expanded_url_title", None)
#             desc = url.get("expanded_url_description", None)
#
#             if display_url or expanded_url:
#
#                 use_url = True
#
#                 if check_if_list_has_text(self.tw_id, [display_url, expanded_url]):
#                     use_url = False
#                 else:
#                     for id in all_secondary_ids:
#                         if check_if_list_has_text(id, [display_url, expanded_url]):
#                             if id in added_statuses:
#                                 # False in all cases, including if we don't want secondary links
#                                 use_url = False
#                             else:
#                                 added_statuses.append(id)
#                                 if not extract_secondary_links:
#                                     use_url = False
#                             break
#
#                 # remove secondary links if necessary
#                 if not extract_secondary_links and \
#                         ((display_url and display_url.lower() in all_secondary_urls) or
#                          (expanded_url and expanded_url.lower() in all_secondary_urls) or
#                          (original_expanded_url and original_expanded_url.lower() in all_secondary_urls)):
#                     use_url = False
#
#                 if use_url:
#                     try:
#                         link = self._create_link(display_url, expanded_url, title, desc)
#                         links.append(link)
#                     except Exception as e:
#                         print e
#                         time.sleep(5)
#                         try:
#                             link = self._create_link(display_url, expanded_url, title, desc)
#                             links.append(link)
#                         except Exception as e:
#                             print "Tried to save link but couldn't (display_url={}, expanded_url={}): {}".format(
#                                 display_url,
#                                 expanded_url,
#                                 e
#                             )
#         return links
#
#
#     def _create_link(self, tw_display_url, tw_expanded_url, title, description):
#
#         if is_not_null(tw_expanded_url):
#
#             if len(tw_expanded_url) > 1000:
#                 tw_expanded_url = tw_expanded_url.split("?")[0]
#
#             good_existing = Link.objects.get_if_exists(
#                 {"tw_display_url": tw_display_url, "tw_expanded_url": tw_expanded_url},
#                 search_nulls=True
#             )
#             bad_existing = Link.objects.get_if_exists(
#                 {"tw_display_url": tw_display_url, "tw_expanded_url": None},
#                 search_nulls=True
#             )
#             if not bad_existing:
#                 bad_existing = Link.objects.get_if_exists(
#                     {"tw_display_url": tw_display_url, "tw_expanded_url": ''},
#                     search_nulls=True
#                 )
#             if bad_existing:
#                 if good_existing:
#                     link = consolidate_objects(source=bad_existing, target=good_existing)
#                 else:
#                     link = bad_existing
#                 link.tw_expanded_url = tw_expanded_url
#                 link.save()
#             else:
#                 link = Link.objects.create_or_update(
#                     {"tw_display_url": tw_display_url, "tw_expanded_url": tw_expanded_url},
#                     search_nulls=True,
#                     save_nulls=True
#                 )
#         else:
#             existing = Link.objects.filter(tw_display_url=tw_display_url, tw_expanded_url=tw_expanded_url)
#             if existing.count() > 1:
#                 keeper = existing[0]
#                 for dupe in existing[1:]:
#                     keeper = consolidate_objects(source=dupe, target=keeper)
#                 link = keeper
#             elif existing.count() == 1:
#                 link = existing[0]
#             else:
#                 link = Link.objects.create_or_update(
#                     {"tw_display_url": tw_display_url, "tw_expanded_url": tw_expanded_url},
#                     search_nulls=True,
#                     save_nulls=True
#                 )
#
#         if title: link.tw_expanded_url_title = title
#         if description: link.tw_expanded_url_description = description
#         link.save()
#
#         # if not link.expanded_url:
#         # link.expand_url()
#
#         return link
#
#     def _format_link(self, link):
#         if link:
#             formatted_link = re.sub("https?:\/\/(www\.)?", "", link)
#             return formatted_link.rstrip('/').lower()
#         else:
#             return None
#
#
# class Link(BasicExtendedModel):
#
#     tw_display_url = models.CharField(max_length=140, null=True, db_index=True)
#     tw_expanded_url = models.CharField(max_length=1000, null=True, db_index=True)
#     tw_expanded_url_title = models.CharField(max_length=250, null=True)
#     tw_expanded_url_description = models.TextField(null=True)
#
#     expanded_url = models.CharField(max_length=1000, null=True, db_index=True)
#
#     domain = models.CharField(max_length=256)
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