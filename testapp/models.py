from django.db import models
from django.conf import settings

from django_twitter.models import *


class Person(models.Model):
    name = models.CharField(max_length=250)


class Organization(models.Model):
    name = models.CharField(max_length=250)


class TwitterProfile(AbstractTwitterProfile):

    person = models.ForeignKey(
        "testapp.Person",
        related_name="twitter_profiles",
        null=True,
        on_delete=models.SET_NULL,
    )
    organization = models.ForeignKey(
        "testapp.Organization",
        related_name="twitter_profiles",
        null=True,
        on_delete=models.SET_NULL,
    )


class TwitterProfileSnapshot(AbstractTwitterProfileSnapshot):

    pass


class Tweet(AbstractTweet):

    pass


class TwitterFollowerList(AbstractTwitterFollowerList):

    pass


class TwitterFollowingList(AbstractTwitterFollowingList):

    pass


class TwitterHashtag(AbstractTwitterHashtag):

    pass


class TweetSet(AbstractTweetSet):

    pass


class TwitterProfileSet(AbstractTwitterProfileSet):

    pass
