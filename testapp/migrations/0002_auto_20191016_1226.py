# -*- coding: utf-8 -*-
# Generated by Django 1.11.25 on 2019-10-16 12:26
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [("testapp", "0001_initial")]

    operations = [
        migrations.RenameField(
            model_name="historicaltweet",
            old_name="user_mentions_raw",
            new_name="profile_mentions_raw",
        ),
        migrations.RenameField(
            model_name="tweet", old_name="user_mentions", new_name="profile_mentions"
        ),
        migrations.RenameField(
            model_name="tweet",
            old_name="user_mentions_raw",
            new_name="profile_mentions_raw",
        ),
        migrations.AlterField(
            model_name="historicaltwitterprofile",
            name="tweet_backfilled",
            field=models.BooleanField(
                default=False,
                help_text="An indicator used in the sync_tweets management function; True indicates that the profile's         tweet history has been backfilled as far as possible, so the sync function will stop after it hits an existing         tweet the next time it runs.",
            ),
        ),
        migrations.AlterField(
            model_name="twitterprofile",
            name="politician",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="twitter_profiles",
                to="testapp.Politician",
            ),
        ),
        migrations.AlterField(
            model_name="twitterprofile",
            name="tweet_backfilled",
            field=models.BooleanField(
                default=False,
                help_text="An indicator used in the sync_tweets management function; True indicates that the profile's         tweet history has been backfilled as far as possible, so the sync function will stop after it hits an existing         tweet the next time it runs.",
            ),
        ),
    ]
