# coding=utf-8
from django.test import TestCase
from StringIO import StringIO
from django.core.management import call_command
import sys


# Tests for weird usernames with special characters for single users and multiple users
class UsernameTestCase(TestCase):
    def setUp(self):
        self.lst_special_users = [['kum@r_pankhur!', "u'code': 50"],
                                  [3248746387, "Successfully saved profile data for kumar_pankhuri"],
                                  ['emma&f', "u'code': 50"]]  # testing
        self.lst_suspended_users = [('GarryLissette', "u'code': 63"),
                                    ('trebortwo', "u'code': 63"),
                                    ('howellatme__', "u'code': 63")]
        self.lst_inactive_users = [['makwechel', "u'code': 50"],
                                   ['DaraStern', "u'code': 50"],
                                   ['RdblancoDavid', "u'code': 50"]]
        # Private Users are still found by get_user, will be required for tweet-testing
        self.lst_private_users = [['Brandontaylr', "Successfully saved profile data for brandontaylr"],
                                  ['lexieroe', "Successfully saved profile data for lexieroe"],
                                  ['Fabsagalicious', "Successfully saved profile data for fabsagalicious"]]

        self.lst_longscreenname = [['CJSWomeninMedia', "Successfully saved profile data for cjswomeninmedia"]]
        # Tweepy doesn't search by username, so this will always return a 'Not Found' error
        self.lst_longusername = [['Budget Low-Price Elainovision', "u'code': 50"]]
        # TODO: Need to find more
        # Empty users are still found by get_user, will be required for tweet-testing
        self.lst_empty_users = [['ChiragY34928202', "Successfully saved profile data for chiragy34928202"]]
        # TODO: run these usernames from test suite
        # Tweepy doesn't search by username, so this will always return a 'Not Found' error
        self.lst_special_usernames = ['Gökçe Özcan', 'Nureen • Social Edit', '💫Shanon Lee 💫']

    def test_user(self):
        saved_stdout = sys.stdout
        sys.stdout = self.out = StringIO()

        self.push_assert(self.lst_special_users)
        self.push_assert(self.lst_suspended_users)
        self.push_assert(self.lst_inactive_users)
        self.push_assert(self.lst_private_users)
        self.push_assert(self.lst_longscreenname)
        self.push_assert(self.lst_longusername)
        self.push_assert(self.lst_empty_users)

        sys.stdout = saved_stdout
        self.out.close()

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

        call_command('django_twitter_get_users', *lst_multi_users, stdout=out)
        self.assertIn("Collecting profile data for 14 users\n1 users found", out.getvalue())
        sys.stdout = saved_stdout
        out.close()

    def push_assert(self, lst):
        for user, expected_output in lst:
            call_command('django_twitter_get_user', user, stdout=self.out)
            self.out.seek(0)
            self.assertIn(expected_output, self.out.getvalue())
            self.out.truncate(0)

if __name__ == '__main__':
    TestCase.main()
