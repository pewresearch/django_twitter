# from future import standard_library
# standard_library.install_aliases()
# import sys
# from django.conf import settings
# from django.core.management import call_command
# from django.apps import apps
# from django.test import TestCase
# from io import StringIO
#
#
# class MultipleUser(TestCase):
#     def setUp(self):
#         self.lst_test_users = []
#
#     def test_multiple_users(self):
#         call_command("django_twitter_get_user_following", "pankhurikumar23")
#         all_users = apps.get_model(app_label=settings.TWITTER_APP,
#                                         model_name=settings.TWITTER_PROFILE_MODEL).objects.all()
#
#         saved_stdout = sys.stdout
#         sys.stdout = out = StringIO()
#
#         out.seek(0)
#         for user in all_users[:50]:
#             self.lst_test_users.append(user.twitter_id)
#         call_command('django_twitter_get_users', *self.lst_test_users, stdout=out)
#         self.assertIn("Collecting profile data for 50 users", out.getvalue())
#
#         for user in all_users[:200]:
#             self.lst_test_users.append(user.twitter_id)
#         call_command('django_twitter_get_users', *self.lst_test_users, stdout=out)
#         self.assertIn("Collecting profile data for 250 users", out.getvalue())
#
#         sys.stdout = saved_stdout
#         out.close()
#
#     def test_data_storage(self):
#         self.lst_test_users = [2538128774, 94573568, 1734045566, 14606079, 469182585, 25561952, 2320134098, 19761853]
#         call_command('django_twitter_get_users', *self.lst_test_users)
#
#         db_all_users = apps.get_model(app_label=settings.TWITTER_APP,
#                                    model_name=settings.TWITTER_PROFILE_MODEL).objects.all()
#         for user in db_all_users:
#             self.assertIn(int(user.twitter_id), self.lst_test_users)