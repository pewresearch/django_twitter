import django, tweepy, json

from django.conf import settings
from django.core.management.base import BaseCommand
from django.apps import apps
from multiprocessing import Pool

from pewtils.django import reset_django_connection
from pewhooks.twitter import TwitterAPIHandler


class Command(BaseCommand):

    def add_arguments(self, parser):

        parser.add_argument("--tweet_set", type = str)
        parser.add_argument('--num_cores', type=int, default=2)
        parser.add_argument('--queue_size', type=int, default=500)
        parser.add_argument('--keyword_query', type=str)

        parser.add_argument('--api_key', type=str)
        parser.add_argument('--api_secret', type=str)
        parser.add_argument('--access_token', type=str)
        parser.add_argument('--access_secret', type=str)

    def handle(self, *args, **options):

        self.twitter = TwitterAPIHandler(
            api_key=options["api_key"],
            api_secret=options["api_secret"],
            access_token=options["access_token"],
            access_secret=options["access_secret"]
        )

        tweet_set = None
        if options["tweet_set"]:
            tweet_set_model = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWEET_SET_MODEL)
            tweet_set, created = tweet_set_model.objects.get_or_create(name=options["tweet_set"])

        listener = StreamListener(
            tweet_set=tweet_set,
            num_cores=options["num_cores"],
            queue_size=options["queue_size"]
        )

        self.twitter.capture_stream_sample(listener, async=False, keywords=options['keyword_query'])


class StreamListener(tweepy.StreamListener):

    def __init__(
        self,
        tweet_set=None,
        num_cores=2,
        queue_size=500
    ):

        self.tweet_set = tweet_set
        self.queue_size = queue_size

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
                self.tweet_queue.append(tweet_json)
                if len(self.tweet_queue) >= self.queue_size:
                    if self.num_cores > 1:
                        self.pool.apply_async(save_tweets, args=[
                            list(self.tweet_queue),
                            self.tweet_set.pk if self.tweet_set else None
                        ])
                    else:
                        self.pool.apply(save_tweets, args=[
                            list(self.tweet_queue),
                            self.tweet_set.pk if self.tweet_set else None
                        ])
                    self.tweet_queue = []
                    self.processed_counter += self.queue_size
                    print "{} tweets scanned, {} sent for processing".format(self.scanned_counter,
                                                                             self.processed_counter)
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

def save_tweets(tweets, tweet_set_id):

    reset_django_connection("dippybird")

    tweet_model = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWEET_MODEL)
    tweet_set = None
    if tweet_set_id:
        tweet_set_model = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWEET_SET_MODEL)
        tweet_set = tweet_set_model.objects.get(pk=tweet_set_id)
    success, error = 0, 0
    for tweet_json in tweets:
        try:
            tweet, created = tweet_model.objects.get_or_create(twitter_id=tweet_json['id_str'])
            tweet.update_from_json(tweet_json)
            if tweet_set:
                tweet_set.tweets.add(tweet)
            success += 1
        except django.db.utils.IntegrityError:
            error += 1

    print "{} tweets saved, {} errored".format(success, error)

    return True