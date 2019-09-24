from __future__ import print_function
from django.core.management.base import BaseCommand, CommandError
from rookery_journalism.models import TwitterUser

import pandas as pd


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--file", required=True, help="csv file with user names/ids"
        )
        parser.add_argument(
            "--user_id_column", default="user_id", help="column name with user id"
        )
        parser.add_argument(
            "--screen_name_column",
            default="screen_name",
            help="column name with screen name",
        )

    def handle(self, *args, **options):
        df = pd.read_csv(options["file"])

        # check if the req'd columns are in the csv file loaded in
        if not set([options["user_id_column"], options["screen_name_column"]]).issubset(
            set(df.columns)
        ):
            raise ValueError(
                "user_id_column and screen_name_column must be valid columns in passed in file"
            )

        # Otherwise, load
        else:
            i = 0
            for index, row in df.iterrows():
                i += 1
                user = {
                    "user_id": row[options["user_id_column"]],
                    "screen_name": row[options["screen_name_column"]],
                }
                print("{}:{}".format(i, user["screen_name"]))
                TwitterUser.objects.update_or_create(**user)
