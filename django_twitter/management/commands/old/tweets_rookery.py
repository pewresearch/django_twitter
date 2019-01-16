from __future__ import unicode_literals
from django.core.management.base import BaseCommand, CommandError
from django.db.utils import DataError
from pewtils.internal.http import canonical_link
from rookery_journalism.functions import Twitter
from rookery_journalism.models import TwitterUser, TwitterTweet, TwitterList, TwitterSearch, TwitterLink, TwitterPlace


class Command(BaseCommand):
    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required = True)
        group.add_argument('--get', action = 'store_true', default = False)

        iteratorGroup = parser.add_mutually_exclusive_group()
        iteratorGroup.add_argument('--since-id')
        iteratorGroup.add_argument('--max-id')

        getGroup = parser.add_mutually_exclusive_group()

        queryGroup = getGroup.add_argument_group()
        queryGroup.add_argument('--list-id')
        queryGroup.add_argument('--owner-id')
        queryGroup.add_argument('--owner-screen-name')
        queryGroup.add_argument('--slug')

        searchGroup = getGroup.add_argument_group()
        searchGroup.add_argument('--search')

        userGroup = getGroup.add_argument_group()
        userGroup.add_argument('--user-id')
        userGroup.add_argument('--user-screen-name')

    def handle(self, *args, **options):
        def consumeTimeline(params):
            def putTweet(item):
                userRecord  = twitter.generateRecord('user', item)
                tweetRecord = twitter.generateRecord('tweet', item)
                placeRecord = twitter.generateRecord('place', item) if hasattr(item.place, 'id') else None

                if placeRecord:
                    try:
                        tPlace, _ = TwitterPlace.objects.update_or_create(**placeRecord)

                    except DataError as e:
                        tPlace = None
                        print e
                        print placeRecord
                else:
                    tPlace = None

                try:
                    tUser, _ = TwitterUser.objects.update_or_create(**userRecord)

                    try:
                        tweetRecord['user'] = tUser
                        if tPlace: tweetRecord['place'] = tPlace
                        tTweet, _ = TwitterTweet.objects.update_or_create(**tweetRecord)
                        if tPlace: tPlace.tweets.add(tTweet)
                        tUser.tweets.add(tTweet)

                    except DataError as e:
                        print e
                        print tweetRecord

                except DataError as e:
                    print e
                    print userRecord

                print tTweet.user.user_id, tTweet.tweet_id, tTweet.created_at

                for link in [
                    u['expanded_url'] if 'expanded_url' in u else u['url']
                    for u in item.entities['urls']
                ]:
                    try:
                        link = canonical_link(link)
                        tLink, _ = TwitterLink.objects.update_or_create(full = link)
                        tLink.tweets.add(tTweet)

                    except DataError as e:
                        print e
                        print link

                return tTweet, tUser

            if 'since_id' in params:
                timelineDirection = 'since_id'
                twitterParams = { 'since_id': params['since_id'] }

            elif 'max_id' in params:
                timelineDirection = 'max_id'
                twitterParams = { 'max_id': params['max_id'] }

            else:
                timelineDirection = None
                twitterParams = {}

            if timelineDirection:
                maxId = 0
                minId = 0

            if 'list' in params:
                twitterParams['list_id'] = params['list'].list_id
                print twitterParams
                for item in twitter.Cursor(twitter.api.list_timeline, **twitterParams).items():
                    tTweet, tUser = putTweet(item)
                    if timelineDirection:
                        maxId = tTweet.tweet_id if tTweet.tweet_id > maxId else maxId
                        minId = tTweet.tweet_id if tTweet.tweet_id < minId else minId
                    params['list'].members.add(tUser)
                    params['list'].tweets.add(tTweet)

            elif 'search' in params:
                twitterParams['q'] = params['search'].query
                print twitterParams
                for item in twitter.Cursor(twitter.api.search, **twitterParams).items():
                    tTweet, tUser = putTweet(item)
                    if timelineDirection:
                        maxId = tTweet.tweet_id if tTweet.tweet_id > maxId else maxId
                        minId = tTweet.tweet_id if tTweet.tweet_id < minId else minId
                    params['search'].tweets.add(tTweet)
                    for tList in TwitterList.objects.filter(list_id__in = tUser.lists.values_list('list_id')):
                        tList.tweets.add(tTweet)

            elif 'user' in params:
                twitterParams['user_id'] = params['user'].user_id
                print twitterParams
                for item in twitter.Cursor(twitter.api.user_timeline, **twitterParams).items():
                    tTweet, tUser = putTweet(item)
                    if timelineDirection:
                        maxId = tTweet.tweet_id if tTweet.tweet_id > maxId else maxId
                        minId = tTweet.tweet_id if tTweet.tweet_id < minId else minId
                    for tList in TwitterList.objects.filter(list_id__in = tUser.lists.values_list('list_id')):
                        tList.tweets.add(tTweet)

            if timelineDirection:
                if timelineDirection == 'since_id' and params[timelineDirection] > 0 and maxId > 0:
                    params[timelineDirection] = maxId
                    print("Consuming timeline {} {}".format(timelineDirection, params[timelineDirection]))
                    consumeTimeline(params)
                elif timelineDirection == 'max_id' and params[timelineDirection] > 1 and minId > 1:
                    params[timelineDirection] = minId - 1
                    print("Consuming timeline {} {}".format(timelineDirection, params[timelineDirection]))
                    consumeTimeline(params)

        if options['get']:
            paramError = CommandError('For searches, --search is required; for users, --user-screen-name or --user-id is required; for lists, at least --list-id, or both --slug and either --owner-id or --owner-screen-name, is required.')

            params = { 'search': TwitterSearch.objects.filter(name = options['search']).first() } \
                if options['search'] \
                else { 'user': TwitterUser.objects.filter(user_id = options['user_id']).first() } \
                    if options['user_id'] \
                    else { 'user': TwitterUser.objects.filter(screen_name = options['user_screen_name']).first() } \
                        if options['user_screen_name'] \
                        else { 'list': TwitterList.objects.filter(list_id = options['list_id']).first() } \
                            if options['list_id'] \
                            else {
                                'list': TwitterList.objects.filter(
                                    slug = options['slug'],
                                    owner__user_id = options['owner_id']
                                ).first()
                            } \
                                if options['slug'] and options['owner_id'] \
                                else {
                                    'list': TwitterList.objects.filter(
                                        slug = options['slug'],
                                        owner__screen_name = options['owner_screen_name']
                                    ).first()
                                } \
                                    if options['slug'] and options['owner_screen_name'] \
                                    else None

            if not params: raise paramError

            if options['since_id']:
                params['since_id'] = options['since_id'] \
                    if options['since_id'] != 'auto' \
                    else TwitterTweet.objects.filter(lists = params['list']).order_by('-tweet_id').first().tweet_id \
                        if 'list' in params \
                        else TwitterTweet.objects.filter(searches = params['search']).order_by('-tweet_id').first().tweet_id \
                            if 'search' in params \
                            else TwitterTweet.objects.filter(user = params['user']).order_by('-tweet_id').first().tweet_id \
                                if 'user' in params \
                                else None

            elif options['max_id']:
                params['max_id'] = options['max_id'] \
                    if options['max_id'] != 'auto' \
                    else TwitterTweet.objects.filter(lists = params['list']).order_by('tweet_id').first().tweet_id \
                        if 'list' in params \
                        else TwitterTweet.objects.filter(searches = params['search']).order_by('tweet_id').first().tweet_id \
                            if 'search' in params \
                            else TwitterTweet.objects.filter(user = params['user']).order_by('tweet_id').first().tweet_id \
                                if 'user' in params \
                                else None

            twitter = Twitter()
            consumeTimeline(params)