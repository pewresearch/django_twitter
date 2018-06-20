# TODO unable to find and populate all_users (line 15)
# TODO Current error: "CommandError: Error: too few arguments" originating at line 27

import sys
from django.conf import settings
from django.core.management import call_command
from django.apps import apps
from django.test import TestCase
from StringIO import StringIO


class MultipleUser(TestCase):
    def setUp(self):
        max_users = 50
        self.lst_test_users = []
        all_users = apps.get_model(app_label=settings.TWITTER_APP,
                                   model_name=settings.TWITTER_PROFILE_MODEL).objects.all()
        for user in all_users[:max_users]:
            # if (user.screen_name is None) and not user.twitter_id == 'galenstocking':  # temp test
                self.lst_test_users.append(user.twitter_id)

    def test_multiple_users(self):
        saved_stdout = sys.stdout
        sys.stdout = out = StringIO()
        self.lst_test_users.append('-V')
        print(self.lst_test_users)
        call_command('django_twitter_get_users', *(self.lst_test_users), stdout=out)

        out.seek(0)
        self.assertIn("Collecting profile data for 3 users\n"
                      "0it [00:00, ?it/s]Collecting user emmagf"
                      "Successfully saved profile data for emmagf: http://twitter.com/emmagf"
                      "Collecting user GalenStocking"
                      "Successfully saved profile data for galenstocking: http://twitter.com/galenstocking"
                      "Collecting user kumar_pankhuri"
                      "Successfully saved profile data for kumar_pankhuri: http://twitter.com/kumar_pankhuri"
                      "1it [00:00,  5.19it/s]"
                      "3 users found", out.getvalue())

        sys.stdout = saved_stdout
        out.close()


if __name__ == '__main__':
    TestCase.main()
