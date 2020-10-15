# Generated by Django 3.1.2 on 2020-10-15 08:33

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testapp', '0006_auto_20200929_0936'),
    ]

    operations = [
        migrations.AlterField(
            model_name='botometerscore',
            name='json',
            field=models.JSONField(default=dict, null=True),
        ),
        migrations.AlterField(
            model_name='historicaltweet',
            name='json',
            field=models.JSONField(default=dict, null=True),
        ),
        migrations.AlterField(
            model_name='historicaltweet',
            name='links',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=400), help_text='Links contained in the tweet', null=True, size=None),
        ),
        migrations.AlterField(
            model_name='historicaltweet',
            name='media',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.JSONField(null=True), help_text='Media contained in the tweet', null=True, size=None),
        ),
        migrations.AlterField(
            model_name='historicaltwitterprofilesnapshot',
            name='contributors_enabled',
            field=models.BooleanField(null=True),
        ),
        migrations.AlterField(
            model_name='historicaltwitterprofilesnapshot',
            name='is_protected',
            field=models.BooleanField(null=True),
        ),
        migrations.AlterField(
            model_name='historicaltwitterprofilesnapshot',
            name='is_verified',
            field=models.BooleanField(null=True),
        ),
        migrations.AlterField(
            model_name='historicaltwitterprofilesnapshot',
            name='json',
            field=models.JSONField(default=dict, null=True),
        ),
        migrations.AlterField(
            model_name='tweet',
            name='json',
            field=models.JSONField(default=dict, null=True),
        ),
        migrations.AlterField(
            model_name='tweet',
            name='links',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=400), help_text='Links contained in the tweet', null=True, size=None),
        ),
        migrations.AlterField(
            model_name='tweet',
            name='media',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.JSONField(null=True), help_text='Media contained in the tweet', null=True, size=None),
        ),
        migrations.AlterField(
            model_name='twitterprofilesnapshot',
            name='contributors_enabled',
            field=models.BooleanField(null=True),
        ),
        migrations.AlterField(
            model_name='twitterprofilesnapshot',
            name='is_protected',
            field=models.BooleanField(null=True),
        ),
        migrations.AlterField(
            model_name='twitterprofilesnapshot',
            name='is_verified',
            field=models.BooleanField(null=True),
        ),
        migrations.AlterField(
            model_name='twitterprofilesnapshot',
            name='json',
            field=models.JSONField(default=dict, null=True),
        ),
    ]