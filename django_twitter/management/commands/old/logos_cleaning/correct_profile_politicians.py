# import datetime
#
# from django.db.models import Count
# from tqdm import tqdm
#
# from pewtils.django import consolidate_objects
# from pewtils import flatten_list
#
# from logos.models import TwitterProfile, Politician, Tweet
# from logos.utils.constants import nonpolitician_twitter_profile_ids
#
# from django_commander.commands import BasicCommand, log_command
#
#
# class Command(BasicCommand):
#
#     parameter_names = []
#     dependencies = []
#
#     @log_command
#     def run(self):
#
#         print "Removing non-politician associations"
#
#         pols = Politician.objects.exclude(twitter_ids__len=0) | Politician.objects.exclude(old_twitter_ids__len=0)
#         nonpol_ids = nonpolitician_twitter_profile_ids()
#         for pol in pols:
#             pol.twitter_ids = list(set(pol.twitter_ids).difference(set(nonpol_ids)))
#             pol.old_twitter_ids = list(set(pol.old_twitter_ids).difference(set(nonpol_ids)))
#             pol.save()
#
#         for sn in nonpolitician_twitter_profile_ids():
#             profiles = TwitterProfile.objects.filter(screen_name__iregex=r"^{0}$".format(sn)) | TwitterProfile.objects.filter(twitter_id__iregex=r"^{0}$".format(sn))
#             if profiles.count() == 1:
#                 profile = profiles[0]
#                 bad_ids = set([profile.twitter_id, profile.screen_name, profile.screen_name.lower()])
#                 if profile.politician:
#                     profile.politician.twitter_ids = list(set(profile.politician.twitter_ids).difference(bad_ids))
#                     profile.politician.old_twitter_ids = list(set(profile.politician.old_twitter_ids).difference(bad_ids))
#                     profile.politician.save()
#                     profile.politician = None
#                     profile.save()
#             elif profiles.count() > 0:
#                 print "Multiple accounts found for {}".format(sn)
#                 import pdb
#                 pdb.set_trace()
#             else:
#                 pass
#
#
#         print "Correcting known misassociations"
#
#         for twitter_id, correct_pol in [
#             ("111635980", 101),
#             ("72198806", 36),
#             ("76069325", 296),
#             ("33563161", 324),
#             ("308721230", 5864),
#             ("235289157", 5882),
#             ("16789970", 288),
#             ("15281676", 246),
#             ("1055907624", 420),
#             ("1048784496", 432),
#             ("156703580", 803),
#             ("1068691076", None),
#             ("52401729", None),
#             ("96017515", None),
#             ("280837107", None),
#             ("255689737", None),
#             ("17375519", None),
#             ("5741722", None)
#         ]:
#
#             # print "Correcting {}".format(twitter_id)
#
#             for bad_pol in Politician.objects.filter(twitter_ids__contains=[twitter_id]).exclude(pk=correct_pol):
#                 bad_pol.twitter_ids = [f for f in bad_pol.twitter_ids if f != twitter_id]
#                 bad_pol.old_twitter_ids = [f for f in bad_pol.old_twitter_ids if f != twitter_id]
#                 bad_pol.save()
#
#             if correct_pol: correct_pol = Politician.objects.get(pk=correct_pol)
#             try:
#                 good_profile = TwitterProfile.objects.get(twitter_id=twitter_id, politician=correct_pol)
#             except TwitterProfile.DoesNotExist:
#                 good_profile = None
#             bad_profiles = TwitterProfile.objects.filter(twitter_id=twitter_id).exclude(politician=correct_pol)
#             if good_profile and bad_profiles.count() == 0:
#                 pass
#             else:
#                 for bad_profile in bad_profiles:
#                     if bad_profile.politician:
#                         bad_profile.politician.twitter_ids = [id for id in bad_profile.politician.twitter_ids if id != twitter_id]
#                         bad_profile.politician.old_twitter_ids = [id for id in bad_profile.politician.old_twitter_ids if
#                                                                 id != twitter_id]
#                         bad_profile.politician.save()
#                     bad_profile.verifications.all().delete()
#                 if not good_profile:
#                     good_profile = bad_profiles[0]
#                     bad_profiles = bad_profiles.exclude(pk=good_profile.pk)
#                 good_profile.verifications.all().delete()
#                 for bad_profile in bad_profiles:
#                     print "Consolidating {} into {}".format(bad_profile, good_profile)
#                     try:
#                         good_profile = consolidate_objects(source=bad_profile, target=good_profile)
#                     except Exception as e:
#                         good_profile = consolidate_objects(source=good_profile, target=bad_profile)
#                 good_profile.politician = correct_pol
#                 good_profile.save()
#                 good_profile.history.update(politician_id=correct_pol.pk if correct_pol else correct_pol)
#                 if good_profile.politician and twitter_id not in good_profile.politician.twitter_ids and twitter_id not in good_profile.politician.old_twitter_ids:
#                     good_profile.politician.twitter_ids.append(twitter_id)
#                     good_profile.politician.save()
#             if good_profile:
#                 if good_profile.politician:
#                     good_profile.history.update(politician_id=good_profile.politician.pk)
#                 else:
#                     good_profile.history.update(politician_id=None)
#
#
#         print "Scanning for non-politician/politician profile duplicates by ID"
#
#         for profile in tqdm(TwitterProfile.objects.filter(politician__isnull=True), desc="Checking non-politician accounts"):
#             pol_profiles = TwitterProfile.objects.filter(twitter_id=profile.twitter_id).exclude(politician__isnull=True)
#             if pol_profiles.count() == 1:
#                 print "Non-politician account {} has a duplicate politician account {}, consolidating to the latter".format(
#                     profile,
#                     pol_profiles[0]
#                 )
#                 consolidate_objects(source=profile, target=pol_profiles[0])
#             elif pol_profiles.count() > 1:
#                 import pdb
#                 pdb.set_trace()
#                 print "This non-pol ID also has multiple pol accounts: {}".format(profile.twitter_id, pol_profiles)
#
#         # TODO: check for any verifications where is_official == None
#
#
#         print "Checking for null/blank Twitter IDs"
#
#         profiles = TwitterProfile.objects.filter(twitter_id__in=[None, "", "None"])
#         if profiles.count() > 0:
#             import pdb
#             pdb.set_trace()
#         tweets = Tweet.objects.filter(twitter_id__in=[None, "", "None"])
#         if tweets.count() > 0:
#             import pdb
#             pdb.set_trace()
#
#
#         print "Correcting time-specific multi-politician accounts"
#
#         time_specific_accounts = {
#             "19739126": [
#                 {"politician_id": 829, "start_date": datetime.date(2006, 2, 2), "end_date": datetime.date(2011, 1, 2)}, # Boehner
#                 {"politician_id": 5952, "start_date": datetime.date(2011, 1, 3), "end_date": datetime.date(2014, 7, 30)}, # Eric Cantor
#                 {"politician_id": 232, "start_date": datetime.date(2014, 7, 31), "end_date": None}, #McCarthy
#             ]
#         }
#         for twitter_id in time_specific_accounts.keys():
#             tweets = Tweet.objects.filter(profile__twitter_id=twitter_id)
#             for row in time_specific_accounts[twitter_id]:
#                 profile = TwitterProfile.objects.get(twitter_id=twitter_id, politician_id=row["politician_id"])
#                 if row["end_date"]:
#                     tweets.filter(timestamp__date__gte=row["start_date"], timestamp__date__lte=row["end_date"]).update(profile=profile)
#                     profile.historical = True
#                     profile.save()
#                 else:
#                     tweets.filter(timestamp__date__gte=row["start_date"]).update(profile=profile)
#
#         # for twitter_id, historical_pol_id in [
#         #     ("19739126", 829),
#         #     ("19739126", 5952)
#         # ]:
#         #     TwitterProfile.objects.create_or_update(
#         #         {"twitter_id": twitter_id, "politician_id": historical_pol_id},
#         #         {"historical": True},
#         #         return_object=False
#         #     )
#
#         print "Scanning for additional multi-politician accounts"
#
#         for row in TwitterProfile.objects.exclude(twitter_id__in=time_specific_accounts.keys())\
#                 .values("twitter_id").annotate(c=Count("politician_id")).filter(c__gt=1):
#             profiles = TwitterProfile.objects.filter(twitter_id=row["twitter_id"])
#             print "Warning: multiple profiles for ID {}: {}".format(row["twitter_id"], profiles.values("politician_id", "screen_name", "politician__last_name", "twitter_id"))
#
#
#         print "Checking for IDs associated with multiple politicians"
#
#         all_twitter_ids = flatten_list(list(Politician.objects.values_list("twitter_ids", flat=True))) + flatten_list(list(Politician.objects.values_list("old_twitter_ids", flat=True)))
#         for twitter_id in list(set(all_twitter_ids)):
#             pols = Politician.objects.filter(twitter_ids__contains=[twitter_id]) | Politician.objects.filter(old_twitter_ids__contains=[twitter_id])
#             if pols.count() > 1:
#                 print "Multiple politicians with the Twitter ID {}".format(twitter_id)
#                 print pols
#                 import pdb
#                 pdb.set_trace()