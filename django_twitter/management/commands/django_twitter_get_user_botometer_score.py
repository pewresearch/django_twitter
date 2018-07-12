from django.conf import settings
from django.core.management.base import BaseCommand
from django.apps import apps


from pewhooks.twitter import TwitterAPIHandler
from pewhooks.botometer_wrapper import  BotometerAPIHandler

class Command(BaseCommand):

    def add_arguments(self, parser):

        parser.add_argument("twitter_ids", nargs="+")


        parser.add_argument("--twitter_profile_set", type=str)
        parser.add_argument('--api_key', type=str)
        parser.add_argument('--api_secret', type=str)
        parser.add_argument('--access_token', type=str)
        parser.add_argument('--access_secret', type=str)
        parser.add_argument('--botometer_key', type=str)

    def handle(self, *args, **options):

        self.twitter = TwitterAPIHandler(
            api_key=options["api_key"],
            api_secret=options["api_secret"],
            access_token=options["access_token"],
            access_secret=options["access_secret"],
        )

        self.botometer = BotometerAPIHandler(
            twitter_api_key=options["api_key"],
            twitter_api_secret=options["api_secret"],
            twitter_access_token=options["access_token"],
            twitter_access_secret=options["access_secret"],
            botometer_key=options["botometer_key"]
        )


        # setup models
        if options["twitter_profile_set"]:
            twitter_profile_set_model = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWITTER_PROFILE_SET_MODEL)
            twitter_profile_set, created = twitter_profile_set_model.objects.get_or_create(name=options["twitter_profile_set"])
        user_model = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWITTER_PROFILE_MODEL)
        botometer_model = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.BOTOMETER_SCORE_MODEL)

        # Get Botometer scores first
        df_botometer_scores = self.botometer.get_botometer_scores(options["twitter_ids"], full_results=True, results_2018=True)

        if not len(df_botometer_scores) > 0:
            raise ValueError("No results returned from Botometer")
        else:
            for twitter_id in options["twitter_ids"]:
                twitter_user, created = user_model.objects.get_or_create(twitter_id=twitter_id)
                score = botometer_model.objects.create(profile=twitter_user)
                score.update_from_dict(df_botometer_scores.query('original_user=="{}"'.format(twitter_id)).iloc[0].to_dict(),
                                       api_version=2)

                if twitter_profile_set:
                    twitter_profile_set.profiles.add(twitter_user)





