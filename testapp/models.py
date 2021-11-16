from django.db import models
from django.conf import settings

from django_twitter.models import *


class Politician(models.Model):

    pass


if settings.TWITTER_APP == "testapp":

    class TwitterProfile(AbstractTwitterProfile):

        politician = models.ForeignKey(
            "testapp.Politician",
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
