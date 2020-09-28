# Generated by Django 3.0.2 on 2020-09-22 11:46

import json
from django.db import migrations, models
from django_twitter.utils import get_concrete_model
from tqdm import tqdm


def add_is_protected_field(apps, schema_editor):
    profile_snapshot_model = get_concrete_model("AbstractTwitterProfileSnapshot")
    TwitterProfileSnapshotModel = apps.get_model(profile_snapshot_model._meta.app_label, profile_snapshot_model._meta.model_name)

    for snapshot_id in tqdm(list(TwitterProfileSnapshotModel.objects.values_list("pk", flat=True)),
                           desc="Adding is_protected field"):
        snapshot = TwitterProfileSnapshotModel.objects.get(pk=snapshot_id)
        while isinstance(snapshot.json, str):
            # For some reason, the JSONField doesn't de-serialize the JSON all of the time, so if it's a string, we'll parse it into proper JSON
            snapshot.json = json.loads(snapshot.json)
        snapshot.is_protected = snapshot.json['protected']
        snapshot.save()


class Migration(migrations.Migration):

    dependencies = [
        ('testapp', '0004_follower_following_lists'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='historicaltwitterprofilesnapshot',
            name='is_private',
        ),
        migrations.RemoveField(
            model_name='twitterprofilesnapshot',
            name='is_private',
        ),
        migrations.AddField(
            model_name='historicaltwitterprofilesnapshot',
            name='is_protected',
            field=models.NullBooleanField(),
        ),
        migrations.AddField(
            model_name='twitterprofilesnapshot',
            name='is_protected',
            field=models.NullBooleanField(),
        ),
        migrations.RunPython(add_is_protected_field),
    ]
