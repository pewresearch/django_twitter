# coding=utf-8
from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
from django.test import TestCase
from django.conf import settings
from django.apps import apps
from io import StringIO
from django.core.management import call_command
import sys


class UsernameTestCase(TestCase):
    # 50: user not found/inactive
    # 63: user suspended
    # private and users with no tweets are found by get_user
    lst_special_users = [['kum@r_pankhur!', "u'code': 50"],
                              [3248746387, "Successfully saved profile data for pankhurikumar23"],
                              ['emma&f', "u'code': 50"]]
    lst_suspended_users = [('GarryLissette', "u'code': 63"),
                                ('trebortwo', "u'code': 63"),
                                ('howellatme__', "u'code': 63")]
    lst_inactive_users = [['makwechel', "u'code': 50"],
                               ['DaraStern', "u'code': 50"],
                               ['RdblancoDavid', "u'code': 50"]]
    lst_private_users = [['Brandontaylr', "Successfully saved profile data for brandontaylr"],
                              ['lexieroe', "Successfully saved profile data for lexieroe"],
                              ['Fabsagalicious', "Successfully saved profile data for fabsagalicious"]]
    lst_longscreenname = [['CJSWomeninMedia', "Successfully saved profile data for cjswomeninmedia"]]
    lst_empty_users = [['ChiragY34928202', "Successfully saved profile data for chiragy34928202"],
                            ['shubhir45767777', "Successfully saved profile data for shubhir45767777"],
                            ['g3hbee', "Successfully saved profile data for g3hbee"]]
    # Tweepy doesn't search by username, will always return a 'Not Found' error
    lst_longusername = [['Budget Low-Price Elainovision', "u'code': 50"]]
    # Tweepy doesn't search by username, will always return a 'Not Found' error
    lst_special_usernames = [[u"Gökçe Özcan", "Successfully saved profile data for"],
                                  [u'Nureen • Social Edit', "xx"],
                                  [u'💫Shanon Lee 💫',"xx"]]
    # Testing the permanent fields of the profile
    fields = [["screen_name", "pankhurikumar23"],
              ["name", "Pankhuri Kumar"],
              ["created_at", "Thu Jun 18 12:49:49 +0000 2015"],
              ["lang", "en"]]
    # lst_working = ["pankhurikumar23", "galenstocking", "pvankessel"]

    def test_user(self):
        saved_stdout = sys.stdout
        sys.stdout = self.out = StringIO()

        self.lst_assert(self.lst_special_users)
        self.lst_assert(self.lst_suspended_users)
        self.lst_assert(self.lst_inactive_users)
        self.lst_assert(self.lst_private_users)
        self.lst_assert(self.lst_longscreenname)
        self.lst_assert(self.lst_empty_users)
        self.lst_assert(self.lst_longusername)
        # self.lst_assert(self.lst_special_usernames)

        sys.stdout = saved_stdout
        self.out.close()

    def lst_assert(self, lst):
        for test_pair in lst:
            user = test_pair[0]
            expected_output = test_pair[1]
            call_command('django_twitter_get_user', user, stdout=self.out)
            self.out.seek(0)
            self.assertIn(expected_output, self.out.getvalue())
            self.out.truncate(0)

    def test_users(self):
        saved_stdout = sys.stdout
        sys.stdout = out = StringIO()

        lst_multi_users = [item[0] for item in self.lst_special_users]
        lst_interim = [item[0] for item in self.lst_suspended_users]
        lst_multi_users.extend(lst_interim)
        lst_interim = [item[0] for item in self.lst_inactive_users]
        lst_multi_users.extend(lst_interim)
        lst_interim = [item[0] for item in self.lst_private_users]
        lst_multi_users.extend(lst_interim)
        lst_interim = [item[0] for item in self.lst_longscreenname]
        lst_multi_users.extend(lst_interim)
        lst_interim = [item[0] for item in self.lst_longusername]
        lst_multi_users.extend(lst_interim)
        lst_interim = [item[0] for item in self.lst_empty_users]
        lst_multi_users.extend(lst_interim)

        call_command('django_twitter_get_users', *lst_multi_users, stdout=out)
        self.assertIn("Collecting profile data for 17 users\n1 users found", out.getvalue())
        sys.stdout = saved_stdout
        out.close()

    def test_storage(self):
        names = ["TanaHillman1", "steventodd214", "lisettevoytko", "Lizalis54491902", "GarryLissette", "3248746387", "earthquakesSF"]
        for user in names:
            call_command('django_twitter_get_user', user)

        users = apps.get_model(app_label=settings.TWITTER_APP,
                              model_name=settings.TWITTER_PROFILE_MODEL).objects.all()
        print(len(users))

        for user in users:
            self.assertIsNotNone(user.twitter_id)
            self.assertIsNotNone(user.created_at)
            self.assertIsNotNone(user.followers_count)
            self.assertIsNotNone(user.description)
            self.assertIsNotNone(user.favorites_count)
            self.assertIsNotNone(user.screen_name)
