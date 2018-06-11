# import tweepy, datetime, time, re
#
# from tqdm import tqdm
#
# from logos.models import TwitterProfile, TwitterFollow, Date, Politician, Tweet
# from pewtils import is_not_null
# from pewtils.twitter import TwitterAPIHandler
#
# from django_commander.commands import IterateDownloadCommand
#
#
# class Command(IterateDownloadCommand):
#
#     """
#     """
#
#     @staticmethod
#     def add_arguments(parser):
#         parser.add_argument("--profile_twitter_id", default=None, type=str)
#         parser.add_argument("--politicians_only", default=False, action="store_true")
#         parser.add_argument("--congress_members_only", default=False, action="store_true")
#         parser.add_argument("--hydrate_users", default=False, action="store_true")
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
#         profiles = TwitterProfile.objects.filter(historical=False)
#         if self.options["profile_twitter_id"]:
#             profiles = profiles.filter(twitter_id=self.options["profile_twitter_id"])
#         elif self.options["politicians_only"]:
#             profiles = profiles.filter(politician_id__isnull=False)
#         elif self.options["congress_members_only"]:
#             profiles = profiles.filter(politician__in=Politician.objects.us_congress_members())
#
#         for profile in tqdm(profiles.order_by("?"), desc="Iterating over politicians"):
#             yield [profile, ]
#             if self.options["test"]: break
#
#     def download(self, source_profile):
#
#         print "Scanning {}".format(source_profile)
#         counter = 0
#         self.date = Date.objects.create_or_update({"date": datetime.datetime.now().date()})
#         for profile_data in self.api.iterate_user_friends(source_profile.twitter_id, hydrate_users=self.options["hydrate_users"]):
#
#             if self.options["hydrate_users"]:
#                 profile_id = profile_data.id_str
#                 timestamp = profile_data.created_at
#                 profile_data = profile_data._json
#             else:
#                 profile_id = profile_data
#
#             profiles = TwitterProfile.objects.filter(historical=False).filter(twitter_id=profile_id)
#             if profiles.count() == 0:
#                 profile = TwitterProfile.objects.create_or_update({"twitter_id": profile_id})
#                 profiles = [profile]
#
#             for profile in profiles:
#
#                 if self.options["hydrate_users"]:
#                     profile = TwitterProfile.objects.create_or_update(
#                         {"pk": profile.pk},
#                         {
#                             "created_at": timestamp,
#                             "json": profile_data
#                         },
#                         save_nulls=True
#                     )
#
#                 profile.command_logs.add(self.log)
#                 profile.commands.add(self.log.command)
#                 follow = TwitterFollow.objects.create_or_update(
#                     {"friend": profile, "follower": source_profile}
#                 )
#                 follow.dates.add(self.date)
#
#             counter += 1
#
#             if counter % 10 == 0:
#                 print "{} follows {} ({} active friends total)".format(source_profile, profile, counter)
#
#         return [None, ]
#
#     def cleanup(self):
#
#         pass
