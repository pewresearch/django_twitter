import tweepy
import django
import datetime
import json

from multiprocessing import Pool

from tweepy import Status, User

from dateutil.parser import parse as parse_date
from urlparse import urlparse

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from pewtils.twitter import TwitterAPIHandler
from pewtils.io import FileHandler
from pewtils.django import reset_django_connection

from dippybird.models import Tweet, Link, KeywordQuery


class Command(BaseCommand):

    def add_arguments(self, parser):

        parser.add_argument('--keyword_query_name', type=str, default=None)
        parser.add_argument('--links_only', action="store_true", default=False)
        parser.add_argument('--extract_secondary_links', action="store_true", default=False)
        parser.add_argument('--use_s3', action="store_true", default=False)
        parser.add_argument('--num_cores', type=int, default=2)
        parser.add_argument('--queue_size', type=int, default=500)

    def handle(self, *args, **options):

        twitter = TwitterAPIHandler(
            api_key=settings.TWITTER_API_KEY,
            api_secret=settings.TWITTER_API_SECRET,
            access_token=settings.TWITTER_ACCESS_TOKEN,
            access_secret=settings.TWITTER_ACCESS_SECRET
        )

        if options["keyword_query_name"]:
            kw_query = KeywordQuery.objects.get(name=options["keyword_query_name"])
            query = kw_query.query
        else:
            kw_query = None
            query = None
        listener = StreamListener(
            kw_query=kw_query,
            links_only=options["links_only"],
            num_cores=options["num_cores"],
            queue_size=options["queue_size"],
            use_s3=options["use_s3"],
            extract_secondary_links=options["extract_secondary_links"]
        )

        twitter.capture_stream_sample(listener, async=False, keywords=query)


class StreamListener(tweepy.StreamListener):

    def __init__(self,
        kw_query=None,
        links_only=False,
        num_cores=2,
        queue_size=500,
        use_s3=False,
        extract_secondary_links=False
    ):

        self.links_only = links_only
        self.kw_query = kw_query
        self.queue_size = queue_size
        self.use_s3 = use_s3
        self.extract_secondary_links = extract_secondary_links

        self.tweet_queue = []
        self.pool = Pool(processes=num_cores)
        self.num_cores = num_cores
        self.scanned_counter = 0
        self.processed_counter = 0
        # self.old_count = Tweet.objects.count()

        super(StreamListener, self).__init__(self)
        print "Stream initialized"

    def on_data(self, data):

        try:

            tweet_json = json.loads(data)

            if 'delete' in tweet_json:
                delete = tweet_json['delete']['status']
                if self.on_delete(delete['id'], delete['user_id']) is False:
                    return False
            elif 'limit' in tweet_json:
                if self.on_limit(tweet_json['limit']['track']) is False:
                    return False
            elif 'disconnect' in tweet_json:
                if self.on_disconnect(tweet_json['disconnect']) is False:
                    return False
            elif 'warning' in tweet_json:
                if self.on_warning(tweet_json['warning']) is False:
                    return False
            else:

                self.scanned_counter += 1

                urls = tweet_json.get("entities", {}).get("urls", [])

                if not self.links_only or len(urls) > 0:
                    self.tweet_queue.append(tweet_json)
                    if len(self.tweet_queue) >= self.queue_size:
                        if self.num_cores > 1:
                            self.pool.apply_async(save_tweets, args=[
                                list(self.tweet_queue),
                                self.links_only,
                                self.kw_query.pk if self.kw_query else None,
                                self.use_s3,
                                self.extract_secondary_links
                            ])
                        else:
                            self.pool.apply(save_tweets, args=[
                                list(self.tweet_queue),
                                self.links_only,
                                self.kw_query.pk if self.kw_query else None,
                                self.use_s3,
                                self.extract_secondary_links
                            ])
                        self.tweet_queue = []
                        self.processed_counter += self.queue_size
                        print "{} tweets scanned, {} sent for processing".format(self.scanned_counter, self.processed_counter)
                        # new_count = Tweet.objects.count()
                        # processed = new_count - self.old_count
                        # print "100 new tweets queued, {} processed since last time".format(processed)
                        # self.old_count = new_count

        except Exception as e:

            print "UNKNOWN ERROR: {}".format(e)
            import pdb
            pdb.set_trace()

        return True

    def on_timeout(self):
        print 'Snoozing Zzzzzz'
        return

    def on_limit(self, limit_data):
        # print "Twitter rate-limited this query.  Since query start, Twitter dropped %d messages." % (limit_data)
        self.omitted_counter = limit_data
        return

    def on_warning(self, warning):
        print "WARNING: {}".format(warning)
        return

    def on_disconnect(self, disconnect):
        print "DISCONNECT: {}".format(disconnect)
        import pdb
        pdb.set_trace()

    def on_error(self, status):

        if status == 420:
            return False
        return

        # print("ERROR: {}".format(status))
        # return False


def save_tweets(tweets, links_only, kw_query_id, use_s3, extract_secondary_links):

    reset_django_connection("dippybird")

    if use_s3:

        h = FileHandler("tweets/{}".format("full_stream" if not kw_query_id else kw_query_id),
            use_s3=True,
            bucket=settings.S3_BUCKET,
            aws_access=settings.AWS_ACCESS_KEY_ID,
            aws_secret=settings.AWS_SECRET_ACCESS_KEY
        )
        h.write(str(datetime.datetime.now()), tweets, format="json")

    else:

        success, skip, error = 0, 0, 0
        for tweet_json in tweets:

            try:
                tweet = Tweet.objects.create_or_update(
                    {"tw_id": tweet_json["id_str"]},
                    {"json": tweet_json}
                )
            except Exception as e:
                tweet = Tweet.objects.get(tw_id=tweet_json["id_str"])
            if kw_query_id:
                tweet.keyword_queries.add(kw_query_id)

            links = tweet.extract_links(extract_secondary_links=extract_secondary_links)

            try:

                if len(links) > 0:

                    tweet.links = links
                    tweet.save()
                    success += 1

                elif links_only:

                    tweet.delete()
                    skip += 1

            except django.db.utils.IntegrityError:
                error += 1

        print "{} tweets saved, {} skipped, {} errored".format(success, skip, error)

    return True