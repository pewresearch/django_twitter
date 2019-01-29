from __future__ import print_function
from django.core.management.base import BaseCommand, CommandError
from rookery_journalism.functions import Twitter
from rookery_journalism.models import TwitterUser, TwitterTweet, TwitterList

class Command(BaseCommand):
    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required = True)
        group.add_argument('--add', action = 'store_true', default = False)
        group.add_argument('--delete', action = 'store_true', default = False)
        group.add_argument('--update', action = 'store_true', default = False)

        listGroup = group.add_argument_group()
        listGroup.add_argument('--list-id')
        listGroup.add_argument('--owner-id')
        listGroup.add_argument('--owner-screen-name')
        listGroup.add_argument('--slug')

    def handle(self, *args, **options):
        paramError = CommandError(
            'At least --list-id, or both --slug and either --owner-id or --owner-screen-name, is required.')

        if options['list_id']:
            params = { 'list_id': options['list_id'] }

        elif options['slug']:
            params = { 'slug': options['slug'] }

            if options['owner_id']:
                params['owner_id'] = options['owner_id']

            elif options['owner_screen_name']:
                params['owner_screen_name'] = options['owner_screen_name']

            else:
                raise paramError

        else:
            raise paramError

        twitter = Twitter()

        if any(options[x] for x in ('add', 'update')):
            twitterData = twitter.api.get_list(**params)
            userRecord  = twitter.generateRecord('user', twitterData)
            listRecord  = twitter.generateRecord('list', twitterData)
            print(listRecord)

            if options['add']:
                tUser, _ = TwitterUser.objects.get_or_create(**userRecord)
                TwitterList.objects.get_or_create(owner = tUser, **listRecord)

            elif options['update']:
                tUser, _ = TwitterUser.objects.update_or_create(**userRecord)
                TwitterList.objects.update_or_create(owner = tUser, **listRecord)

        if options['delete']:
            raise CommandError("Not implemented!")
