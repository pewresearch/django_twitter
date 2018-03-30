from dateutil.parser import parse as date_parse
from django.db.models import Q

from logos.models import Tweet, TwitterProfile, Year, State
from logos.utils.constants import nonpolitician_twitter_profile_ids
from django_learning.models import Document
from pewtils import is_not_null, is_null
from pewtils.django import consolidate_objects
from pewtils.twitter import TwitterAPIHandler

from django_commander.commands import IterateDownloadCommand


class TwitterCommand(IterateDownloadCommand):
    
    def __init__(self, **options):

        self.nonpol_ids = nonpolitician_twitter_profile_ids()
        self.api = TwitterAPIHandler()

        super(TwitterCommand, self).__init__(**options)

    def clean_politician_twitter_ids(self, pol):

        # Just to make sure, lowercase all screen_names, and convert them to permanent IDs wherever possible
        # Since screen_names can change and get recycled
        pol.twitter_ids = [f.lower().split(".")[0] if f.endswith(".0") else f.lower() for f in pol.twitter_ids if
                            f not in ['none', 'None', None] and f not in self.nonpol_ids and "e+" not in str(f)]
        pol.old_twitter_ids = [f.lower().split(".")[0] if f.endswith(".0") else f.lower() for f in pol.old_twitter_ids
                                if f not in ['none', 'None', None] and f not in self.nonpol_ids and "e+" not in str(f)]
        pol.save()
        for profile in pol.twitter_profiles.all():
            if profile.screen_name:
                profile.screen_name = profile.screen_name.lower()
                profile.save()
            if profile.historical and profile.twitter_id not in pol.old_twitter_ids:
                pol.old_twitter_ids.append(profile.twitter_id)
                pol.save()
            elif not profile.historical and profile.twitter_id not in pol.twitter_ids:
                pol.twitter_ids.append(profile.twitter_id)
                pol.save()
        for row in pol.twitter_profiles.values("twitter_id", "screen_name"):
            if is_not_null(row['screen_name']):
                if row["screen_name"] in pol.twitter_ids:
                    pol.twitter_ids = list(set([f for f in pol.twitter_ids if f != row['screen_name']] + [row['twitter_id']]))
                if row["screen_name"] in pol.old_twitter_ids:
                    pol.old_twitter_ids = list(set([f for f in pol.old_twitter_ids if f != row['screen_name']] + [row['twitter_id']]))
                pol.save()

        return pol

    def update_tweet_from_api_object(self, t, profile, prev_id=None):

        tweet = self.get_unique_tweet(t['id'], profile, prev_id=prev_id)

        timestamp = date_parse(t['created_at'])
        tweet = Tweet.objects.create_or_update(
            {"pk": tweet.pk},
            {
                "twitter_id": t["id_str"],
                "timestamp": timestamp,
                "year": Year.objects.create_or_update({"id": timestamp.year}, command_log=self.log),
                "json": t
            },
            search_nulls=False,
            save_nulls=True,
            empty_lists_are_null=True,
            command_log=self.log
        )

        text = t['text'].encode("utf-8")
        if is_not_null(text):
            Document.objects.create_or_update(
                {"tweet": tweet},
                {
                    "text": text,
                    "original_text": text,
                    "is_clean": False,
                    "date": tweet.created_at
                },
                return_object=False,
                save_nulls=False,
                command_log=self.log
            )

        tweet.update_from_json()
        
        return tweet
    
    def get_unique_tweet(self, id, profile, prev_id=None):

        try:
            tweet = Tweet.objects.create_or_update(
                {"twitter_id": id, "profile": profile},
            )
        except Exception as e:
            print e
            import pdb
            pdb.set_trace()
        ids = list(set([id, tweet.twitter_id] + tweet.duplicate_twitter_ids))
        if prev_id and prev_id not in ids: ids.append(prev_id)
        existing = tweet.source_profile.feed \
            .filter(Q(twitter_id__in=ids) | Q(duplicate_twitter_ids__overlap=ids)).distinct()

        if existing.count() > 1:
            if existing.filter(twitter_id=id).count() == 0:
                tweet.duplicate_twitter_ids = list(set(tweet.duplicate_twitter_ids + [tweet.twitter_id]))
                tweet.twitter_id = id
                tweet.save()
                keeper = tweet
            else:
                keeper = existing.get(twitter_id=id)
            dupe_ids = []
            for dupe in existing.exclude(pk=keeper.pk):
                print "Deduplicating {} -> {}".format(dupe, keeper)
                dupe_ids.append(dupe.twitter_id)
                if is_null(dupe.document) or is_null(keeper.document):
                    keeper = consolidate_objects(source=dupe, target=keeper)
                else:
                    try:
                        dupe_doc = dupe.document
                        dupe.document = None
                        dupe.save()
                        keep_doc = consolidate_objects(source=dupe_doc, target=keeper.document)
                        keep_doc.save()
                        keeper.document = keep_doc
                        keeper.save()
                        keeper = consolidate_objects(source=dupe, target=keeper)
                    except Exception as e:
                        print e
                        import pdb
                        pdb.set_trace()
            tweet = Tweet.objects.get(pk=keeper.pk)
            tweet.duplicate_twitter_ids = list(set(tweet.duplicate_twitter_ids + dupe_ids))
            tweet.save()
        else:
            tweet = existing[0]

        return tweet

    def update_profile_from_api_object(self, p, politician, prev_id=None):

        profile = self.get_unique_profile(p['id'], politician, prev_id=prev_id)

        profile = TwitterProfile.objects.create_or_update(
            {"pk": profile.pk},
            {"json": p},
            save_nulls=True,
            empty_lists_are_null=True,
            command_log=self.log
        )

        # if is_not_null(p['description']):
        #     Document.objects.create_or_update(
        #         {"twitter_profile": profile},
        #         {
        #             "text": p['description'],
        #             "original_text": p['description'],
        #             "is_clean": True,
        #             "date": date_parse(p['created_at'])
        #         },
        #         return_object=False,
        #         command_log=self.log
        #     )

        profile.update_from_json()
        profile.update_tweets_official_status()

        return profile

    def get_unique_profile(self, id, politician, prev_id=None):

        try:
            profile = TwitterProfile.objects.create_or_update(
                {"twitter_id": id, "politician": politician},
            )
        except Exception as e:
            import pdb
            pdb.set_trace()
        ids = list(set([id, profile.twitter_id] + profile.duplicate_twitter_ids))
        if prev_id and prev_id not in ids: ids.append(prev_id)
        existing = TwitterProfile.objects.filter(politician=profile.politician) \
            .filter(Q(twitter_id__in=ids) | Q(duplicate_twitter_ids__overlap=ids)).distinct()

        if existing.count() > 1:
            print "Duplicates found"
            import pdb
            pdb.set_trace()
            if existing.filter(twitter_id=id).count() == 0:
                profile.duplicate_twitter_ids = list(set(profile.duplicate_twitter_ids + [profile.twitter_id]))
                profile.twitter_id = id
                profile.save()
                keeper = profile
            else:
                keeper = existing.get(twitter_id=id)
            dupe_ids = []
            for dupe in existing.exclude(pk=keeper.pk):
                dupe_ids.append(dupe.twitter_id)
                if any([dupe.is_official, keeper.is_official]):
                    is_official = True
                else:
                    is_official = False
                if dupe.tweet_backfill and keeper.tweet_backfill:
                    tweet_backfill = True
                else:
                    tweet_backfill = False
                keeper = consolidate_objects(source=dupe, target=keeper, overwrite=False)
                keeper.is_official = is_official
                keeper.tweet_backfill = tweet_backfill
                keeper.save()
            profile = TwitterProfile.objects.get(pk=keeper.pk)
            profile.duplicate_twitter_ids = list(set(profile.duplicate_twitter_ids + dupe_ids))
            profile.save()
        else:
            profile = existing[0]

        if hasattr(profile, "politician") and is_not_null(profile.politician):
            if profile.twitter_id not in profile.politician.twitter_ids:
                profile.politician.twitter_ids.append(profile.twitter_id)
            if profile.twitter_id in profile.politician.old_twitter_ids:
                profile.politician.old_twitter_ids = [i for i in profile.politician.old_twitter_ids if
                                                    i != profile.twitter_id]
            profile.politician.old_twitter_ids = list(
                set(profile.politician.old_twitter_ids).union(set(profile.duplicate_twitter_ids)))
            profile.politician.save()

        return profile