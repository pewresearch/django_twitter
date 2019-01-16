import os, json, glob, re, pandas

from multiprocessing.pool import Pool
from tqdm import tqdm

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db.utils import IntegrityError

from pewtils import decode_text, chunker
from django_pewtils import reset_django_connection

from dippybird.models import Tweet, Link


class Command(BaseCommand):

    def add_arguments(self, parser):

        parser.add_argument("--refresh_existing", action="store_true", default=False)
        parser.add_argument("--gnip_only", action="store_true", default=False)
        parser.add_argument("--no_gnip", action="store_true", default=False)
        parser.add_argument("--domain_whitelist_only", action="store_true", default=False)
        parser.add_argument("--extract_secondary_links", action="store_true", default=False)
        parser.add_argument("--expand_urls", action="store_true", default=False)
        parser.add_argument('--use_multiprocessing', action='store_true', default=False)
        parser.add_argument("--num_cores", default=2, type=int)
        parser.add_argument("--testing", action='store_true', default=False)

    def handle(self, *args, **options):

        # set retweet pattern
        self.rt_match = re.compile(r'RT @.*: (.*)')

        tweets = Tweet.objects.all()
        if options["gnip_only"]:
            tweets = tweets.filter(gnip=True)
        elif options["no_gnip"]:
            tweets = tweets.filter(gnip=False)
        if options["domain_whitelist_only"]:
            whitelist = pandas.read_csv("domain_master_codes.csv")['domain'].values
            tweets = tweets.filter(links__domain__name__in=whitelist)
        if not options["refresh_existing"]:
            # tweets = tweets.filter(links=None)
            tweets = tweets.filter(last_link_extract_time__isnull=True)

        if not options["use_multiprocessing"]:
            if options['testing']:
                i = 0
                for tweet in tweets.chunk(1000, randomize=True):
                # for tweet in tweets[:100]:
                    if i == 1000:
                        break
                    print("{}:{}".format(tweet.tw_id, tweet))
                    tweet.extract_links(extract_secondary_links=options['extract_secondary_links'],
                                        save=True,
                                        process=options['expand_urls'])
                    print(tweet.links.all())
                    i += 1
            else:
                for tweet in tqdm(tweets.chunk(1000), desc="Rescanning for all links"):
                    tweet.extract_links(extract_secondary_links=options['extract_secondary_links'],
                                        save=True,
                                        process=options['expand_urls'])


        else:

            processed = 0
            for chunk in tqdm(chunker(list(tweets.values_list("pk", flat=True)), 1000 * options["num_cores"]),
                              total=tweets.count() / (1000 * options["num_cores"]), desc="Extracting links"):
                pool = Pool(processes=options["num_cores"])
                if options['num_cores'] == 1:
                    func = pool.apply
                else:
                    func = pool.apply_async
                results = []
                for subchunk in chunker(chunk, 1000):
                    results.append(func(extract_links, [subchunk, options["extract_secondary_links"], options["expand_urls"]]))
                pool.close()
                pool.join()
                try:
                    results = [r.get() for r in results]
                    result_sum = sum(results)
                    processed += result_sum
                    print "{} tweets processed, {} total".format(result_sum, processed)
                except Exception as e:
                    print e

def extract_links(tweet_ids, extract_secondary_links, expand_urls):

    reset_django_connection("dippybird")

    processed = 0

    tweets = Tweet.objects.filter(pk__in=tweet_ids)
    for tweet in tweets:
        tweet.extract_links(extract_secondary_links=extract_secondary_links,
                            save=True,
                            process=expand_urls,
                            refresh=True)
        processed += 1

    return processed
