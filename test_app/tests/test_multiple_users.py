import sys
from django.conf import settings
from django.core.management import call_command
from django.apps import apps
from django.test import TestCase
from StringIO import StringIO


class MultipleUser(TestCase):
    def setUp(self):
        self.lst_test_users = []
        call_command("django_twitter_get_user_friends", "kumar_pankhuri")
        self.all_users = apps.get_model(app_label=settings.TWITTER_APP,
                                   model_name=settings.TWITTER_PROFILE_MODEL).objects.all()

    def test_multiple_users(self):
        saved_stdout = sys.stdout
        sys.stdout = out = StringIO()

        out.seek(0)
        for user in self.all_users[:50]:
            self.lst_test_users.append(user.twitter_id)
        call_command('django_twitter_get_users', *(self.lst_test_users), stdout=out)
        self.assertIn("Collecting profile data for 50 users", out.getvalue())

        for user in self.all_users[:200]:
            self.lst_test_users.append(user.twitter_id)
        call_command('django_twitter_get_users', *(self.lst_test_users), stdout=out)
        self.assertIn("Collecting profile data for 250 users", out.getvalue())

        sys.stdout = saved_stdout
        out.close()


if __name__ == '__main__':
    TestCase.main()
