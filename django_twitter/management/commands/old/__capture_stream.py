from __future__ import print_function
from builtins import str
from django_pewtils import reset_django_connection

from django_twitter.models import Tweet, Link
from pewhooks.twitter import TwitterAPIHandler


class Command(BaseCommand):
    def add_arguments(self, parser):

        parser.add_argument("--keyword_query_name", type=str, default=None)
        parser.add_argument("--links_only", action="store_true", default=False)
        parser.add_argument(
            "--extract_secondary_links", action="store_true", default=False
        )
        parser.add_argument("--use_s3", action="store_true", default=False)
        parser.add_argument("--num_cores", type=int, default=2)
        parser.add_argument("--queue_size", type=int, default=500)

    def handle(self, *args, **options):

        twitter = TwitterAPIHandler(
            api_key=settings.TWITTER_API_KEY,
            api_secret=settings.TWITTER_API_SECRET,
            access_token=settings.TWITTER_ACCESS_TOKEN,
            access_secret=settings.TWITTER_ACCESS_SECRET,
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
            extract_secondary_links=options["extract_secondary_links"],
        )

        twitter.capture_stream_sample(listener, async=False, keywords=query)


def save_tweets(tweets, links_only, kw_query_id, use_s3, extract_secondary_links):

    reset_django_connection("dippybird")

    if use_s3:

        h = FileHandler(
            "tweets/{}".format("full_stream" if not kw_query_id else kw_query_id),
            use_s3=True,
            bucket=settings.S3_BUCKET,
            aws_access=settings.AWS_ACCESS_KEY_ID,
            aws_secret=settings.AWS_SECRET_ACCESS_KEY,
        )
        h.write(str(datetime.datetime.now()), tweets, format="json")

    else:

        success, skip, error = 0, 0, 0
        for tweet_json in tweets:

            try:
                tweet = Tweet.objects.create_or_update(
                    {"tw_id": tweet_json["id_str"]}, {"json": tweet_json}
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

        print("{} tweets saved, {} skipped, {} errored".format(success, skip, error))

    return True
