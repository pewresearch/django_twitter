# import tweepy, datetime, time, re
#
# from tqdm import tqdm
#
# from logos.models import Politician, TwitterProfile, Tweet, Year, TwitterHashtag
# from django_learning.models import Document
# from pewtils import is_not_null
# from pewtils.twitter import TwitterAPIHandler
#
# from django_commander.commands import IterateDownloadCommand
#
#
# class Command(IterateDownloadCommand):
#
#     """
#         Iterates over Politician objects with non-null twitter_id fields, and pulls the latest tweets from their
#         timeline. Once a politician's full timeline has been processed (from what's avaialble), the backfill flag gets
#         set. For politicians with a known backfill, the iterator will break early once it encounters an existing tweet.
#         This ensures that if the syncing process is interrupted before it finishes for a given politician, it will
#         iterate completely the next time the command is run.
#     """
#
#     @staticmethod
#     def add_arguments(parser):
#         parser.add_argument("--ignore_backfill", action="store_true", default=False)
#         parser.add_argument("--overwrite", action="store_true", default=False)
#         parser.add_argument("--bioguide_id", default=None, type=str)
#         parser.add_argument("--profile_id", default=None, type=int)
#         return parser
#
#     parameter_names = []
#     dependencies = [
#         ("load_united_states_github_congress_members", {}),
#         ("load_united_states_github_congress_member_social_media", {}),
#         ("load_twitter_politician_profiles", {})
#     ]
#
#     def __init__(self, **options):
#
#         self.api = TwitterAPIHandler()
#
#         super(Command, self).__init__(**options)
#
#     def iterate(self):
#
#         profiles = TwitterProfile.objects \
#             .filter(politician__isnull=False) \
#             .filter(historical=False) \
#             .order_by("?")
#         if self.options["bioguide_id"]:
#             profiles = profiles.filter(politician__bioguide_id=self.options["bioguide_id"])
#         if self.options["profile_id"]:
#             profiles = profiles.filter(pk=self.options["profile_id"])
#         for profile in tqdm(profiles.distinct(),
#             "Syncing politician Twitter profiles",
#             leave=True
#         ):
#             yield [profile, ]
#             if self.options["test"]: break
#
#     def download(self, profile):
#
#         scanned_count, updated_count = 0, 0
#         existing_tweets = list(profile.tweets.values_list("twitter_id", flat=True))
#         existing_tweets.extend(flatten_list(list(profile.tweets.values_list("duplicate_twitter_ids", flat=True))))
#         for t in tqdm(self.api.iterate_user_timeline(profile.twitter_id), desc="Iterating over tweets for {}".format(str(profile))):
#             if not profile.tweet_backfill or self.options["overwrite"] or self.options["ignore_backfill"] or t['id_str'] not in existing_tweets:
#
#                 if self.options["overwrite"] or t['id_str'] not in existing_tweets:
#
#                     self.update_tweet_from_api_object(t, profile)
#                     updated_count += 1
#
#                 elif profile.tweet_backfill and not self.options["ignore_backfill"]:
#
#                     print "Encountered existing tweet, breaking off now"
#                     break
#
#                 scanned_count += 1
#
#                 existing_tweets.append(t['id_str'])
#
#             else:
#
#                 print "Reached end of backfill, breaking off"
#                 break
#
#         if not self.options["test"]:
#
#             profile.tweet_backfill = True
#             profile.save()
#             profile.command_logs.add(self.log)
#             profile.commands.add(self.log.command)
#
#         print "{}: {} tweets scanned, {} updated".format(str(profile), scanned_count, updated_count)
#
#         return [None, ]
#
#     def cleanup(self):
#
#         pass