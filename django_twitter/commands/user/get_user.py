from django.conf import settings

from django_commender.commands import BasicCommand, commands, log_command
from pewtils.django import get_model

from pewhooks import TwitterAPIHandler

class Command(BasicCommand):

    parameter_names = ["twitter_id"]
    dependencies = []

    @staticmethod
    def add_arguments(parser):
        parser.add_argument("-id", "twitter_id", type=str)

    def __init__(self, **options):
        super(Command, self).__init__(**options)
        self.twitter = TwitterAPIHandler()

    @log_command
    def run(self):
        twitter_json = self.twitter.get_user_tweets(self.parameters["twitter_id"])

        twitter_user = get_model(settings.getattr('TWITTER_USER_MODEL')).objects.create_or_update(
            {'twitter_id': self.parameters['twitter_id']},
            return_object=True
        )
        twitter_user.update_from_json(twitter_json)
