from django.db import models

from django_twitter.models import *


class Politician(models.Model):

    pass

class TwitterProfile(AbstractTwitterProfile):

    politician = models.ForeignKey("test_app.Politician", related_name="twitter_profiles", null=True)

class Tweet(AbstractTweet):

    pass