from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management import call_command



# Tests for weird usernames with special characters for single users and multiple users
class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("-d", "--debug", action="store_true")


    def handle(self, *args, **options):

        if options["debug"]:
            import pdb
            pdb.set_trace()

        lst_bad_users = ['kum@r_pankhuri', 3248746387, 'emma&f']  #testing

        print("Running tests for 'django_twitter_get_user'")
        for user in lst_bad_users:
            call_command('django_twitter_get_user', user)

        print("\n\nRunning tests for 'django_twitter_get_users'")
        call_command('django_twitter_get_users', *lst_bad_users)
