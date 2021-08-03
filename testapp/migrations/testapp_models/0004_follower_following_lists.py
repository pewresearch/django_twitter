# Generated by Django 3.0.2 on 2020-01-14 15:44

from django.db import migrations, models
from django.conf import settings
import django.db.models.deletion
from django.db.models import Min, Max
from tqdm import tqdm
from django_twitter.utils import get_concrete_model


def migrate_followers(apps, schema_editor):
    profile_set_model = get_concrete_model("AbstractTwitterProfileSet")
    TwitterProfileSetModel = apps.get_model(profile_set_model._meta.app_label, profile_set_model._meta.model_name)
    profile_model = get_concrete_model("AbstractTwitterProfile")
    TwitterProfileModel = apps.get_model(profile_model._meta.app_label, profile_model._meta.model_name)
    list_model = get_concrete_model("AbstractTwitterFollowerList")
    TwitterFollowerListModel = apps.get_model(list_model._meta.app_label, list_model._meta.model_name)

    for profile_id in tqdm(list(TwitterProfileModel.objects.values_list("pk", flat=True)),
                           desc="Migrating to follower lists"):
        profile = TwitterProfileModel.objects.get(pk=profile_id)
        for run_id in profile.follower_details.values_list("run_id", flat=True).distinct():
            followers = profile.follower_details.filter(run_id=run_id)
            start_date = followers.aggregate(Min("date"))['date__min']
            finish_date = followers.aggregate(Max("date"))['date__max']
            follower_list = TwitterFollowerListModel.objects.create(profile_id=profile.pk)
            follower_list.followers.set(list(followers.values_list("follower__pk", flat=True)))
            follower_list.start_time = start_date
            follower_list.finish_time = finish_date
            follower_list.save()


def migrate_followings(apps, schema_editor):
    profile_set_model = get_concrete_model("AbstractTwitterProfileSet")
    TwitterProfileSetModel = apps.get_model(profile_set_model._meta.app_label, profile_set_model._meta.model_name)
    profile_model = get_concrete_model("AbstractTwitterProfile")
    TwitterProfileModel = apps.get_model(profile_model._meta.app_label, profile_model._meta.model_name)
    list_model = get_concrete_model("AbstractTwitterFollowingList")
    TwitterFollowingListModel = apps.get_model(list_model._meta.app_label, list_model._meta.model_name)

    for profile_id in tqdm(list(TwitterProfileModel.objects.values_list("pk", flat=True)),
                           desc="Migrating to follower lists"):
        profile = TwitterProfileModel.objects.get(pk=profile_id)
        for run_id in profile.following_details.values_list("run_id", flat=True).distinct():
            followings = profile.following_details.filter(run_id=run_id)
            start_date = followings.aggregate(Min("date"))['date__min']
            finish_date = followings.aggregate(Max("date"))['date__max']
            following_list = TwitterFollowingListModel.objects.create(profile_id=profile.pk)
            following_list.followings.set(list(followings.values_list("following__pk", flat=True)))
            following_list.start_time = start_date
            following_list.finish_time = finish_date
            following_list.save()


class Migration(migrations.Migration):

    dependencies = [
        ('testapp', '0003_twitterprofilesnapshot'),
    ]

    operations = [
        migrations.CreateModel(
            name='TwitterFollowerList',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.DateTimeField(auto_now_add=True)),
                ('finish_time', models.DateTimeField(null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TwitterFollowingList',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.DateTimeField(auto_now_add=True)),
                ('finish_time', models.DateTimeField(null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='twitterfollowinglist',
            name='followings',
            field=models.ManyToManyField(to='testapp.TwitterProfile'),
        ),
        migrations.AddField(
            model_name='twitterfollowinglist',
            name='profile',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE,
                                    related_name='following_lists', to='testapp.TwitterProfile'),
        ),
        migrations.AddField(
            model_name='twitterfollowerlist',
            name='followers',
            field=models.ManyToManyField(to='testapp.TwitterProfile'),
        ),
        migrations.AddField(
            model_name='twitterfollowerlist',
            name='profile',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE,
                                    related_name='follower_lists', to='testapp.TwitterProfile'),
        ),
        migrations.RunPython(migrate_followers),
        migrations.RunPython(migrate_followings),
        migrations.RemoveField(
            model_name='twitterrelationship',
            name='follower',
        ),
        migrations.RemoveField(
            model_name='twitterrelationship',
            name='following',
        ),
        migrations.RemoveField(
            model_name='twitterprofile',
            name='followers',
        ),
        migrations.DeleteModel(
            name='TwitterRelationship',
        ),
    ]