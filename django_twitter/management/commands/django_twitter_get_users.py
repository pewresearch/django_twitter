from django.conf import settings
from django.core.management.base import BaseCommand
from django.apps import apps

from tqdm import tqdm

from pewhooks.twitter import TwitterAPIHandler


class Command(BaseCommand):

    def add_arguments(self, parser):

        parser.add_argument("twitter_ids", nargs="+")

        parser.add_argument("-V", "--verbose", action="store_true") # cannot be lower case to work with call_command
        parser.add_argument("--twitter_profile_set", type=str)

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
        twitter_profile_set = None
        if options["twitter_profile_set"]:
            twitter_profile_set_model = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWITTER_PROFILE_SET_MODEL)
            twitter_profile_set, created = twitter_profile_set_model.objects.get_or_create(name=options["twitter_profile_set"])

        print("Collecting profile data for {} users".format(len(options["twitter_ids"])))
        cnt = 0
        for user_id_block in tqdm(chunker(options['twitter_ids'], 100), total=len(options['twitter_ids'])/100):
            cnt += self.process_users(user_id_block, twitter_profile_set, options['verbose'], cnt)
        print("{} users found".format(cnt))

    def process_users(self, lst_user_ids, twitter_profile_set, verbose, cnt=0):
        # TODO: handle if chunk has weird ids (special characters, spelling errors)
        # TODO: this function leverages the bulk API call but its limitation is that you can't track individual accounts
        # in terms of their suspensions and error codes; for the sake of being thorough, I recommend making this a wrapper around django_twitter_get_user
        lst_json = self.twitter.get_users(lst_user_ids)
        if lst_json is None:
            return cnt

        user_model = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWITTER_PROFILE_MODEL)
        for user_json in lst_json:
            if verbose:
                print("Collecting user {}".format(user_json.screen_name))
            twitter_user, created = user_model.objects.get_or_create(
                twitter_id=user_json.id)
            twitter_user.update_from_json(user_json._json)
            if twitter_profile_set:
                twitter_profile_set.profiles.add(twitter_user)
            if verbose:
                print("Successfully saved profile data for {}".format(str(twitter_user)))
            cnt += 1
        return cnt

def chunker(seq, size):
    return (seq[pos:pos + size] for pos in xrange(0, len(seq), size))