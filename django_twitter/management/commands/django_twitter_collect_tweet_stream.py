from __future__ import print_function
import django, tweepy, json, datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from django.apps import apps
from django import db
from multiprocessing import Pool
from tqdm import tqdm

from django_pewtils import reset_django_connection, reset_django_connection_wrapper
from pewhooks.twitter import TwitterAPIHandler

from django_twitter.utils import get_concrete_model, safe_get_or_create


allowable_limit_types = {
    "minute": ["m", "min", "minutes", "minute"],
    "hour": ["h", "hour", "hours"],
    "day": ["d", "days", "day"],
    "tweet": ["t", "tweets"],
}


class Command(BaseCommand):
    def add_arguments(self, parser):

        parser.add_argument("--num_cores", type=int, default=2)
        parser.add_argument("--queue_size", type=int, default=500)
        parser.add_argument("--keyword_query", type=str)
        parser.add_argument(
            "--limit",
            type=str,
            default="",
            help="Accepts: x tweets, x minutes, x hours, x days",
        )
        parser.add_argument("--test", action="store_true", default=False)

        parser.add_argument("--add_to_tweet_set", type=str)
        parser.add_argument("--add_to_profile_set", type=str)

        parser.add_argument("--api_key", type=str)
        parser.add_argument("--api_secret", type=str)
        parser.add_argument("--access_token", type=str)
        parser.add_argument("--access_secret", type=str)

    def handle(self, *args, **options):

        self.twitter = TwitterAPIHandler(
            api_key=options["api_key"],
            api_secret=options["api_secret"],
            access_token=options["access_token"],
            access_secret=options["access_secret"],
        )

        # determine time / tweets
        self.limit = {}
        if options["limit"] == "":
            # could technically put these above but want to make it more explicit
            self.limit["limit_type"] = None
            self.limit["limit_count"] = None
            self.limit["limit_time"] = None
        else:
            limit_values = options["limit"].split(" ")

            # error checking
            if not len(limit_values) == 2:
                raise ValueError(
                    "Please specify limit in format: <number> <duration/tweets>."
                )
            try:
                temp = int(limit_values[0])
            except:
                raise ValueError("Please specify a number of minutes/days/hours/tweets")

            passed_allowed_limit_type = False
            for limit_type in list(allowable_limit_types.keys()):
                if limit_values[1] in allowable_limit_types[limit_type]:
                    self.limit["limit_type"] = limit_type
                    passed_allowed_limit_type = True
                    break
            if not passed_allowed_limit_type:
                raise ValueError("Please specify limit in appropriate duration.")

            if limit_values[1] in allowable_limit_types["tweet"]:
                self.limit["limit_count"] = int(limit_values[0])
            elif limit_values[1] in allowable_limit_types["minute"]:
                self.limit["limit_time"] = datetime.datetime.now() + datetime.timedelta(
                    minutes=int(limit_values[0])
                )
            elif limit_values[1] in allowable_limit_types["hour"]:
                self.limit["limit_time"] = datetime.datetime.now() + datetime.timedelta(
                    hours=int(limit_values[0])
                )
            elif limit_values[1] in allowable_limit_types["day"]:
                self.limit["limit_time"] = datetime.datetime.now() + datetime.timedelta(
                    days=int(limit_values[0])
                )
            else:
                raise ValueError("Could not set limit")

        listener = StreamListener(
            tweet_set=options["add_to_tweet_set"],
            profile_set=options["add_to_profile_set"],
            num_cores=options["num_cores"],
            queue_size=options["queue_size"],
            limit=self.limit,
            test=options["test"],
        )

        self.twitter.capture_stream_sample(
            listener,
            use_async=False,
            keywords=[options["keyword_query"]] if options["keyword_query"] else None,
        )


class StreamListener(tweepy.StreamListener):
    def __init__(
        self,
        tweet_set=None,
        profile_set=None,
        num_cores=2,
        queue_size=500,
        limit=None,
        test=False,
    ):

        self.tweet_set = tweet_set
        self.profile_set = profile_set
        self.queue_size = queue_size
        self.limit = limit if limit else {}
        self.test = test

        self.tweet_queue = []
        self.pool = Pool(processes=num_cores)
        self.num_cores = num_cores
        self.scanned_counter = 0
        self.processed_counter = 0

        super(StreamListener, self).__init__(self)
        print("Stream initialized")

    def on_data(self, data):

        try:
            tweet_json = json.loads(data)

            if "delete" in tweet_json:
                delete = tweet_json["delete"]["status"]
                if self.on_delete(delete["id"], delete["user_id"]) is False:
                    return False
            elif "limit" in tweet_json:
                if self.on_limit(tweet_json["limit"]["track"]) is False:
                    return False
            elif "disconnect" in tweet_json:
                if self.on_disconnect(tweet_json["disconnect"]) is False:
                    return False
            elif "warning" in tweet_json:
                if self.on_warning(tweet_json["warning"]) is False:
                    return False
            else:

                self.scanned_counter += 1
                self.tweet_queue.append(tweet_json)
                if len(self.tweet_queue) >= self.queue_size:

                    if self.num_cores > 1:
                        self.pool.apply_async(
                            save_tweets,
                            args=[
                                list(self.tweet_queue),
                                self.tweet_set,
                                self.profile_set,
                                self.test,
                            ],
                        )
                    else:
                        self.pool.apply(
                            save_tweets,
                            args=[
                                list(self.tweet_queue),
                                self.tweet_set,
                                self.profile_set,
                                self.test,
                            ],
                        )

                    self.tweet_queue = []
                    self.processed_counter += self.queue_size
                    print(
                        "{} tweets scanned, {} sent for processing".format(
                            self.scanned_counter, self.processed_counter
                        )
                    )
                    if self.limit_exceeded():
                        # wait for db connections
                        self.pool.close()
                        self.pool.join()
                        if not self.test:
                            db.connections.close_all()
                        return False
                    else:
                        return True
                else:
                    return True

        except Exception as e:

            print("UNKNOWN ERROR: {}".format(e))
            import pdb

            pdb.set_trace()

            return True

    def on_timeout(self):
        print("Snoozing Zzzzzz")
        return

    def on_limit(self, limit_data):
        # print("Twitter rate-limited this query.  Since query start, Twitter dropped %d messages." % (limit_data))
        self.omitted_counter = limit_data
        return

    def on_warning(self, warning):
        print("WARNING: {}".format(warning))
        return

    def on_disconnect(self, disconnect):
        print("DISCONNECT: {}".format(disconnect))
        import pdb

        pdb.set_trace()

    def on_error(self, status):

        if status == 420:
            return False
        return

        # print("ERROR: {}".format(status))
        # return False

    def limit_exceeded(self):
        if self.limit["limit_type"] is None:
            return True
        elif self.limit["limit_type"] == "tweet":
            return self.processed_counter >= self.limit["limit_count"]
        else:
            return datetime.datetime.now() >= self.limit["limit_time"]


def save_tweets(tweets, tweet_set, profile_set, test):

    if not test:
        reset_django_connection(settings.TWITTER_APP)

    Tweet = get_concrete_model("AbstractTweet")
    if tweet_set:
        tweet_set = safe_get_or_create(
            "AbstractTweetSet", "name", tweet_set, create=True
        )
    if profile_set:
        profile_set = safe_get_or_create(
            "AbstractTwitterProfileSet", "name", profile_set, create=True
        )

    success, error = 0, 0
    for tweet_json in tweets:
        try:
            tweet = safe_get_or_create(
                "AbstractTweet", "twitter_id", tweet_json["id_str"], create=True
            )
            tweet.update_from_json(tweet_json)
            if tweet_set:
                tweet_set.tweets.add(tweet)
            if profile_set:
                profile_set.profiles.add(tweet.profile)
            success += 1
        except django.db.utils.IntegrityError:
            error += 1

    print("{} tweets saved, {} errored".format(success, error))
    return True
