# from django.test import TestCase
# from django.conf import settings
# from django.apps import apps
# from django.core.management import call_command
#
#
# class FollowersTest(TestCase):
#     def setUp(self):
#         # Uncomment last ID to add user[2] - has common followings with user[0],
#         # will raise errors as no. of followings(user[2]) > no. of followings added for user[2]
#         # since same following has been added for user[0] already
#         self.users = [778119432199700481, 50189730] #, 1007488662098055170]
#         for user in self.users:
#             call_command("django_twitter_get_user", user)
#
#     def test_followers(self):
#         for user in self.users:
#             orig_users = apps.get_model(app_label=settings.TWITTER_APP,
#                                         model_name=settings.TWITTER_PROFILE_MODEL).objects.all()
#             orig = len(orig_users)
#             current_user = apps.get_model(app_label=settings.TWITTER_APP,
#                                           model_name=settings.TWITTER_PROFILE_MODEL).objects.filter(
#                 twitter_id=user)
#             call_command("django_twitter_get_user_followers", user, hydrate=True)
#             all_users = apps.get_model(app_label=settings.TWITTER_APP,
#                                             model_name=settings.TWITTER_PROFILE_MODEL).objects.all()
#             self.assertEqual(len(all_users) - orig, current_user[0].json['followers_count'])
#             for user in all_users:
#                 self.assertIsNotNone(user.twitter_id)
#                 self.assertIsNotNone(user.created_at)
#                 self.assertIsNotNone(user.followers_count)
#                 self.assertIsNotNone(user.description)
#                 self.assertIsNotNone(user.favorites_count)
#                 self.assertIsNotNone(user.screen_name)
#
#
#     def test_following(self):
#         for user in self.users:
#             orig_users = apps.get_model(app_label=settings.TWITTER_APP,
#                                        model_name=settings.TWITTER_PROFILE_MODEL).objects.all()
#             orig = len(orig_users)
#             current_user = apps.get_model(app_label=settings.TWITTER_APP,
#                                           model_name=settings.TWITTER_PROFILE_MODEL).objects.filter(
#                 twitter_id=user)
#             call_command("django_twitter_get_user_following", user)
#             all_users = apps.get_model(app_label=settings.TWITTER_APP,
#                                        model_name=settings.TWITTER_PROFILE_MODEL).objects.all()
#             self.assertEqual(len(all_users) - orig, current_user[0].json['friends_count'])
