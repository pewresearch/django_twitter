# import tweepy, datetime, time, re
#
# from tqdm import tqdm
# from dateutil.parser import parse as date_parse
#
# from logos.models import Politician, TwitterProfile, Tweet, Year
# from logos.utils.constants import nonpolitician_twitter_profile_ids
# from logos.utils.twitter import TwitterCommand
# from django_learning.models import Document
# from pewtils import is_not_null, flatten_list
# from pewtils.django import consolidate_objects
# from pewtils.twitter import TwitterAPIHandler
#
# from django_commander.commands import IterateDownloadCommand, commands
#
#
# class Command(TwitterCommand):
#
#     """
#         Iterates over Politician objects with non-null twitter_id fields, and pulls the latest tweets from their
#         timeline. Once a politician's full timeline has been processed (from what's avaialble), the backfill flag gets
#         set. For politicians with a known backfill, the iterator will break early once it encounters an existing tweet.
#         This ensures that if the syncing process is interrupted before it finishes for a given politician, it will
#         iterate completely the next time the command is run.
#     """
#
#     parameter_names = []
#     dependencies = [
#         ("load_united_states_github_congress_members", {}),
#         ("load_united_states_github_congress_member_social_media", {})
#     ]
#
#     @staticmethod
#     def add_arguments(parser):
#         parser.add_argument("--reset_historical", action="store_true", default=False)
#         parser.add_argument("--pol_id", type=str, default=None)
#         return parser
#
#     def __init__(self, **options):
#
#         self.existing_ids = TwitterProfile.objects.values_list("twitter_id", "politician_id")
#
#         super(Command, self).__init__(**options)
#
#     def iterate(self):
#
#         pols = Politician.objects.exclude(twitter_ids=[]) | Politician.objects.filter(twitter_profiles__isnull=False)
#         if self.options["pol_id"]:
#             pols = pols.filter(pk=self.options["pol_id"])
#         for pol in tqdm(pols.distinct(), desc="Loading politician Twitter profiles", leave=True):
#             yield [pol, ]
#             if self.options["test"]: break
#
#     def download(self, pol):
#
#         pol = self.clean_politician_twitter_ids(pol)
#
#         if self.options["reset_historical"]:
#             pol.twitter_ids = list(set(pol.twitter_ids).union(set(pol.old_twitter_ids)).union(set(list(pol.twitter_profiles.values_list("twitter_id", flat=True)))))
#             pol.old_twitter_ids = []
#             pol.save()
#             pol.twitter_profiles.update(historical=False)
#
#         current_ids = pol.twitter_ids + list(pol.twitter_profiles.filter(historical=False).values_list("twitter_id", flat=True))
#         if self.options["reset_historical"]:
#             current_ids.extend(flatten_list(list(pol.twitter_profiles.filter(historical=False).values_list("duplicate_twitter_ids", flat=True))))
#         current_ids = [i for i in list(set(current_ids)) if i not in ["None", None, ""]]
#
#         print pol
#         print "Active IDs: {}".format(pol.twitter_ids)
#         print "Old IDs: {}".format(pol.old_twitter_ids)
#         print "Profile IDs: {}".format(pol.twitter_profiles.values("twitter_id", "historical"))
#         print "IDs to scan: {}".format(current_ids)
#
#         invalid_ids = []
#         for input_id in current_ids:
#
#             try:
#                 p = self.api.get_user(str(input_id))
#             except ValueError:
#                 p = None
#             if not p:
#                 invalid_ids.append(input_id)
#             else:
#                 p = p._json
#                 if p['id_str'] not in self.nonpol_ids:
#                     self.update_profile_from_api_object(p, pol, prev_id=input_id)
#
#         for id in invalid_ids:
#             if id not in pol.old_twitter_ids:
#                 pol.old_twitter_ids.append(id)
#                 pol.save()
#             if id in pol.twitter_ids:
#                 pol.twitter_ids = [i for i in pol.twitter_ids if i != id]
#                 pol.save()
#             existing = TwitterProfile.objects.get_if_exists({"twitter_id": id, "politician": pol})
#             if existing:
#                 # print "Setting existing profile as historical: {}".format(existing)
#                 existing.historical = True
#                 existing.save()
#                 # TODO: you only want to fill in profile data from tweets if they're more up-to-date than when this profile was last refreshed, or if there are blanks
#                 # tweets = existing.tweets.filter(json__isnull=False).order_by("-timestamp")
#                 # if tweets.count() > 0:
#                 #     profile_data = tweets[0].json['user']
#                 #     profile_data['created_at'] = date_parse(profile_data['created_at'])
#                 #     self.update_profile_from_api_object(profile_data, pol, prev_id=existing.twitter_id)
#
#         print "RESULTS: "
#         print "Active IDs: {}".format(pol.twitter_ids)
#         print "Old IDs: {}".format(pol.old_twitter_ids)
#         print "Profile IDs: {}".format(pol.twitter_profiles.values("twitter_id", "historical"))
#
#         if self.log:
#             pol.command_logs.add(self.log)
#             pol.commands.add(self.log.command)
#
#         return [None, ]
#
#     def cleanup(self):
#
#         commands["clean_twitter_correct_profile_politicians"]().run()
