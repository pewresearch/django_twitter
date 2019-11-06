# -*- coding: utf-8 -*-
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
LOCAL_CACHE_ROOT = "cache"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sites",
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

TWITTER_PROFILE_MODEL = "TwitterProfile"
TWEET_MODEL = "Tweet"
BOTOMETER_SCORE_MODEL = "BotometerScore"
TWITTER_RELATIONSHIP_MODEL = "TwitterRelationship"
TWITTER_HASHTAG_MODEL = "TwitterHashtag"
TWITTER_PLACE_MODEL = "TwitterPlace"
TWEET_SET_MODEL = "TweetSet"
TWITTER_PROFILE_SET_MODEL = "TwitterProfileSet"


# NOTE: right now, you can only test the concrete vs. abstract models by switching the settings below manually

# TWITTER_APP = "django_twitter"
# MIGRATION_MODULES = {"testapp": "testapp.migrations.django_twitter_models"}
TWITTER_APP = "testapp"
MIGRATION_MODULES = {"testapp": "testapp.migrations.testapp_models"}
