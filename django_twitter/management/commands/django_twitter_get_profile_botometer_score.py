from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from pewhooks.twitter import TwitterAPIHandler
from django_twitter.utils import (
    get_twitter_profile_json,
    get_twitter_profile,
    get_twitter_profile_set,
    get_concrete_model,
)


class Command(BaseCommand):
    def add_arguments(self, parser):

        parser.add_argument("twitter_id", type=str)
        parser.add_argument("--add_to_profile_set", type=str)

        parser.add_argument("--api_key", type=str)
        parser.add_argument("--api_secret", type=str)
        parser.add_argument("--access_token", type=str)
        parser.add_argument("--access_secret", type=str)
        parser.add_argument("--botometer_key", type=str)

    def handle(self, *args, **options):

        self.twitter = TwitterAPIHandler(
            api_key=options["api_key"],
            api_secret=options["api_secret"],
            access_token=options["access_token"],
            access_secret=options["access_secret"],
            botometer_key=options["botometer_key"],
        )

        if options["add_to_profile_set"]:
            profile_set = get_twitter_profile_set(options["add_to_profile_set"])
        else:
            profile_set = None

        twitter_json = get_twitter_profile_json(options["twitter_id"], self.twitter)
        if twitter_json:

            twitter_profile = get_twitter_profile(twitter_json.id_str, create=True)
            snapshot = get_concrete_model(
                "AbstractTwitterProfileSnapshot"
            ).objects.create(profile=twitter_profile)
            snapshot.update_from_json(twitter_json._json)
            twitter_profile.twitter_error_code = None
            twitter_profile.save()
            botometer_scores = self.twitter.get_profile_botometer_score(
                options["twitter_id"]
            )
            BotometerScore = get_concrete_model("AbstractBotometerScore")
            score = BotometerScore.objects.create(profile=twitter_profile)
            score.update_from_json(botometer_scores)

            if profile_set:
                profile_set.profiles.add(twitter_profile)
