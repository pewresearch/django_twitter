from __future__ import print_function
from django.core.management.base import BaseCommand, CommandError
from rookery_journalism.models import TwitterSearch


class Command(BaseCommand):
    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--add", action="store_true", default=False)
        group.add_argument("--update", action="store_true", default=False)
        group.add_argument("--delete", action="store_true", default=False)

        searchGroup = group.add_argument_group()
        searchGroup.add_argument("--name", required=True)
        searchGroup.add_argument("--query", required=True)

    def handle(self, *args, **options):
        if any(options[x] for x in ("add", "update")):
            searchRecord = {
                "name": options["name"],
                "defaults": {"query": options["query"]},
            }

            print(searchRecord)

            if options["add"]:
                TwitterSearch.objects.get_or_create(**searchRecord)

            elif options["update"]:
                TwitterSearch.objects.update_or_create(**searchRecord)

        if options["delete"]:
            raise CommandError("Not implemented!")
