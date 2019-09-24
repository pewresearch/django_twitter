from django.db import models

from django_twitter.models import *


class Politician(models.Model):

    pass


class TwitterProfile(AbstractTwitterProfile):

    politician = models.ForeignKey(
        "testapp.Politician",
        related_name="twitter_profiles",
        null=True,
        on_delete=models.SET_NULL,
    )


class Tweet(AbstractTweet):

    pass


class BotometerScore(AbstractBotometerScore):

    pass


class TwitterRelationship(AbstractTwitterRelationship):

    pass


class TwitterHashtag(AbstractTwitterHashtag):

    pass


class TwitterPlace(AbstractTwitterPlace):

    pass


class TweetSet(AbstractTweetSet):

    pass


class TwitterProfileSet(AbstractTwitterProfileSet):

    pass
