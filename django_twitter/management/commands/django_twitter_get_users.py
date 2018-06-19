from django.conf import settings
from django.core.management.base import BaseCommand
from django.apps import apps


from pewhooks.twitter import TwitterAPIHandler

class Command(BaseCommand):

    def add_arguments(self, parser):

        parser.add_argument("twitter_ids", nargs="+")

        parser.add_argument("-v", "--verbose", action="store_true")
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
        if len(options["twitter_ids"]) > 100: # API endpoint can only take 100 users at a time
            for user_block in range((len(options["twitter_ids"]) / 100) + 1):
                lst_json = self.twitter.get_users(options["twitter_ids"])
                for user_json in user_block:
                    if options["verbose"]:
                        print("Collecting user {}".format(user_json.screen_name))
                    user_model = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWITTER_PROFILE_MODEL)
                    twitter_user, created = user_model.objects.get_or_create(twitter_id=user_json.screen_name) # TODO: Verify this is screen name and not id
                    twitter_user.update_from_json(user_json._json)
                    if twitter_profile_set:
                        twitter_profile_set.profiles.add(twitter_user)
                    if options["verbose"]:
                        print("Successfully saved profile data for {}".format(str(twitter_user)))
                    cnt += 1
        print("{} users found".format(cnt))
