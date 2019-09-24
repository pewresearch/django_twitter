from __future__ import print_function
from django.core.management.base import BaseCommand, CommandError
from rookery_journalism.models import TwitterUser


class Command(BaseCommand):
    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--add", action="store_true", default=False)
        group.add_argument("--update", action="store_true", default=False)
        group.add_argument("--delete", action="store_true", default=False)

        userGroup = group.add_argument_group()
        userGroup.add_argument("--user-id")
        userGroup.add_argument("--user-screen-name")

    def handle(self, *args, **options):
        if any(options[x] for x in ("add", "update")):
            userRecord = (
                {"user_id": options["user_id"]}
                if options["user_id"]
                else {"screen_name": options["user_screen_name"]}
            )

            print(userRecord)

            if options["add"]:
                TwitterUser.objects.get_or_create(**userRecord)

            elif options["update"]:
                TwitterUser.objects.update_or_create(**userRecord)

        if options["delete"]:
            raise CommandError("Not implemented!")
