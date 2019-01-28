from __future__ import print_function
from django.core.management.base import BaseCommand, CommandError
from django.db.utils import DataError

from rookery_journalism.functions import Twitter
from rookery_journalism.models import TwitterUser, TwitterPlace, TwitterTweet, TwitterLink

from pewtils.internal.http import canonical_link

from tweepy.error import TweepError
from tqdm import tqdm


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        twitter = Twitter()
        all_users = TwitterUser.objects.all()
        all_users = all_users
        print('Pulling data on all {} users'.format(len(all_users)))

        for user in tqdm(all_users, total=len(all_users)):
            if not user.twitter_error:
                print('************')
                print('************')
                print(user.screen_name)
                print('************')
                print('************')

                try: # a lot of these accounts (around 20%) are suspended
                    timeline = twitter.api.user_timeline(user.user_id)
                except TweepError as e:
                    user.twitter_error = e[0]
                    user.save()
                else:
                    for tweet_object in twitter.Cursor(twitter.api.user_timeline, user_id=user.user_id).items():
                        tTweet, tUser = self._putTweet(twitter, tweet_object, follow_links=False)

    def _putTweet(self, twitter, item, follow_links=False):
        userRecord = twitter.generateRecord('user', item)
        tweetRecord = twitter.generateRecord('tweet', item)
        placeRecord = twitter.generateRecord('place', item) if hasattr(item.place, 'id') else None

        if placeRecord:
            try:
                tPlace, _ = TwitterPlace.objects.update_or_create(**placeRecord)

            except DataError as e:
                tPlace = None
                print(e)
                print(placeRecord)
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
                print(e)
                print(tweetRecord)

        except DataError as e:
            print(e)
            print(userRecord)

        #print tTweet.user.user_id, tTweet.tweet_id, tTweet.created_at

        if follow_links:
            for link in [
                u['expanded_url'] if 'expanded_url' in u else u['url']
                for u in item.entities['urls']
            ]:
                try:
                    link = canonical_link(link)
                    tLink, _ = TwitterLink.objects.update_or_create(full=link)
                    tLink.tweets.add(tTweet)

                except DataError as e:
                    print(e)
                    print(link)

        return tTweet, tUser
