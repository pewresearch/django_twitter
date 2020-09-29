# Generated by Django 3.0.2 on 2020-09-29 09:10

import django.contrib.postgres.fields
from django.db import migrations, models
from tqdm import tqdm
from pewtils import is_not_null


def populate_media_links(apps, schema_editor):

    from django_twitter.utils import get_concrete_model
    import pandas as pd

    # During migrations, Django creates "fake" versions of the models that are accessible via apps
    # So we need to look up the models in our app, and then grab the fake migration-based versions via apps
    TweetModel = None
    model = get_concrete_model("AbstractTweet")
    if model:
        TweetModel = apps.get_model(model._meta.app_label, model._meta.model_name)

    for tweet in tqdm(TweetModel.objects.exclude(json={}).exclude(json__isnull=True),
                        desc="Extracting media links from tweets"):
        media_links = []
        if "extended_entities" in tweet.json.keys():
            for entity in tweet.json.get('extended_entities', {}).get('media', []):
                media_link = entity['media_url_https']
                if is_not_null(media_link):
                    media_links.append(media_link)
        tweet.media_links = list(media_links)
        tweet.save()


class Migration(migrations.Migration):

    dependencies = [
        ('testapp', '0005_auto_20200922_1146'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicaltweet',
            name='media_links',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=400), default=list, help_text='Media links contained in the tweet', null=True, size=None),
        ),
        migrations.AddField(
            model_name='tweet',
            name='media_links',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=400), default=list, help_text='Media links contained in the tweet', null=True, size=None),
        ),
        migrations.RunPython(populate_media_links, migrations.RunPython.noop),
    ]
