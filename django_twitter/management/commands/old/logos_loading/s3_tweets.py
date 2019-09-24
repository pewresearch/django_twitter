# import datetime, time, re
#
# from tqdm import tqdm
# from dateutil.parser import parse as parse_date
# from collections import Counter, defaultdict
# from django.db.models import Q
#
# from logos.models import Politician, TwitterProfile, Tweet, Year
# from django_learning.models import Document
# from pewtils import is_not_null
# from pewtils.io import FileHandler
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
#         parser.add_argument("--update_existing", action="store_true", default=False)
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
#         self.profiles = {}
#
#         self.known_accounts = set(list(TwitterProfile.objects.filter(politician__isnull=False).values_list("twitter_id", flat=True)))
#         for pol in Politician.objects.exclude(twitter_ids=[]):
#             self.known_accounts = self.known_accounts.union(set(pol.twitter_ids))
#         for pol in Politician.objects.exclude(old_twitter_ids=[]):
#             self.known_accounts = self.known_accounts.union(set(pol.old_twitter_ids))
#         self.known_accounts = set([str(a).lower() for a in self.known_accounts])
#
#         self.counter = Counter()
#
#         super(Command, self).__init__(**options)
#
#     def iterate(self):
#
#         batches = ["batch0-logos", "batch1", "batch2", "batch3", "batch4", ]
#         for batch in batches:
#             handler = FileHandler("/mnt/nfs/home/shared/twitter/chunks/{}".format(batch), use_s3=False)
#             for filepath in handler.iterate_path():
#                 if filepath.endswith(".json"):
#                     tweets = handler.read(re.sub(r"\.json", "", filepath), format="json")
#                     for tweet in tweets:
#                         yield [tweet, ]
#                         self.counter["total"] += 1
#                         if self.counter["total"] % 100 == 0:
#                             print "{} chunks scanned, {} tweets updated, {} skipped, {} out of scope ({} profiles identified)".format(
#                                 self.counter["chunks"],
#                                 self.counter["updated"],
#                                 self.counter["skipped"],
#                                 self.counter["out_of_scope"],
#                                 len(self.profiles.keys())
#                             )
#                     self.counter["chunks"] += 1
#
#     def download(self, tweet):
#
#         profile = None
#         account_id = str(tweet['user']['id_str']).lower()
#         # if account_id.endswith(".0"):
#         #     account_id = account_id.split(".")[0]
#         if account_id in self.profiles:
#             profile = self.profiles[account_id]
#         elif account_id in self.known_accounts:
#             try:
#                 profile = TwitterProfile.objects.get_if_exists({"twitter_id": account_id})
#                 self.profiles[account_id] = profile
#             except TwitterProfile.MultipleObjectsReturned:
#                 print "Multiple profiles found for the same ID, not sure which one to use (which pol is this?)"
#                 import pdb
#                 pdb.set_trace()
#             if not profile:
#                 pol = None
#                 try:
#                     pol = Politician.objects.get(Q(twitter_ids__contains=[account_id])|Q(old_twitter_ids__contains=[account_id]))
#                 except Politician.MultipleObjectsReturned:
#                     print "Found more than one politician that has this ID listed as their own"
#                     import pdb
#                     pdb.set_trace()
#                 except Politician.DoesNotExist:
#                     print "Couldn't find any politician with this twitter ID, huh"
#                     import pdb
#                     pdb.set_trace()
#
#                 if pol:
#                     profile = TwitterProfile.objects.create(
#                         twitter_id=account_id,
#                         politician=pol
#                     )
#                     self.profiles[account_id] = profile
#         else:
#             self.counter["out_of_scope"] += 1
#
#         if profile:
#             if self.options["update_existing"] or not Tweet.objects.get_if_exists({"twitter_id": str(tweet["id"])}):
#
#                 timestamp = parse_date(tweet["created_at"])
#
#                 t = Tweet.objects.create_or_update(
#                     {"twitter_id": str(tweet["id"])},
#                     {
#                         "profile": profile,
#                         "timestamp": timestamp,
#                         "year": Year.objects.create_or_update({"id": timestamp.year}, command_log=self.log),
#                         # "text": tweet.text.encode("utf-8"),
#                         "retweet_count": tweet.get("retweet_count", None),
#                         "favorite_count": tweet.get("favorite_count", None),
#                         "json": tweet
#                     },
#                     search_nulls=False,
#                     save_nulls=True,
#                     empty_lists_are_null=True,
#                     command_log=self.log
#                 )
#
#                 try:
#                     links = set(t.links)
#                 except TypeError:
#                     links = set()
#                 for u in tweet.get("entities", {}).get("urls", []):
#                     link = u.get("expanded_url", "")
#                     if len(link) > 399: link = u.get("url", "")
#                     if is_not_null(link):
#                         links.add(link)
#                 t.links = list(links)
#                 t.save()
#
#                 text = tweet.get("text").encode("utf-8")
#                 if is_not_null(text):
#                     Document.objects.create_or_update(
#                         {"tweet": t},
#                         {
#                             "text": text,
#                             "original_text": text,
#                             "is_clean": False,
#                             "date": timestamp
#                         },
#                         return_object=False,
#                         save_nulls=False,
#                         command_log=self.log
#                     )
#
#                 self.counter["updated"] += 1
#
#             else:
#                 self.counter["skipped"] += 1
#
#         return [None, ]
#
#     def cleanup(self):
#
#         pass
