from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("-d", "--debug", action="store_true")


    def handle(self, *args, **options):

        if options["debug"]:
            import pdb
            pdb.set_trace()

        lst_bad_users = ['GökçeÖzcan', 'kumar_pankhuri', 'kum@r_pankhur!']  #testing

        call_command('django_twitter_get_users', lst_bad_users, '-V')
