# -*- coding: utf-8 -*-
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django_twitter",
    "testapp",
]

TEMPLATES = []

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "postgres",
        "USER": "postgres",
        "PASSWORD": "",
        "HOST": "localhost",
        "PORT": "",
    }
}

SECRET_KEY = "testing"

TWITTER_APP = "testapp"
TWITTER_PROFILE_MODEL = "TwitterProfile"
TWEET_MODEL = "Tweet"
BOTOMETER_SCORE_MODEL = "BotometerScore"
TWITTER_RELATIONSHIP_MODEL = "TwitterRelationship"
TWITTER_HASHTAG_MODEL = "TwitterHashtag"
TWITTER_PLACE_MODEL = "TwitterPlace"
TWEET_SET_MODEL = "TweetSet"
TWITTER_PROFILE_SET_MODEL = "TwitterProfileSet"
