# Generated by Django 3.0.2 on 2020-02-20 15:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('testapp', '0003_historicaltwitterprofilesnapshot_twitterprofilesnapshot'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='historicaltwitterprofile',
            name='contributors_enabled',
        ),
        migrations.RemoveField(
            model_name='historicaltwitterprofile',
            name='description',
        ),
        migrations.RemoveField(
            model_name='historicaltwitterprofile',
            name='favorites_count',
        ),
        migrations.RemoveField(
            model_name='historicaltwitterprofile',
            name='followers_count',
        ),
        migrations.RemoveField(
            model_name='historicaltwitterprofile',
            name='followings_count',
        ),
        migrations.RemoveField(
            model_name='historicaltwitterprofile',
            name='is_private',
        ),
        migrations.RemoveField(
            model_name='historicaltwitterprofile',
            name='is_verified',
        ),
        migrations.RemoveField(
            model_name='historicaltwitterprofile',
            name='json',
        ),
        migrations.RemoveField(
            model_name='historicaltwitterprofile',
            name='listed_count',
        ),
        migrations.RemoveField(
            model_name='historicaltwitterprofile',
            name='location',
        ),
        migrations.RemoveField(
            model_name='historicaltwitterprofile',
            name='name',
        ),
        migrations.RemoveField(
            model_name='historicaltwitterprofile',
            name='profile_image_url',
        ),
        migrations.RemoveField(
            model_name='historicaltwitterprofile',
            name='status',
        ),
        migrations.RemoveField(
            model_name='historicaltwitterprofile',
            name='statuses_count',
        ),
        migrations.RemoveField(
            model_name='historicaltwitterprofile',
            name='urls',
        ),
        migrations.RemoveField(
            model_name='twitterprofile',
            name='contributors_enabled',
        ),
        migrations.RemoveField(
            model_name='twitterprofile',
            name='description',
        ),
        migrations.RemoveField(
            model_name='twitterprofile',
            name='favorites_count',
        ),
        migrations.RemoveField(
            model_name='twitterprofile',
            name='followers_count',
        ),
        migrations.RemoveField(
            model_name='twitterprofile',
            name='followings_count',
        ),
        migrations.RemoveField(
            model_name='twitterprofile',
            name='is_private',
        ),
        migrations.RemoveField(
            model_name='twitterprofile',
            name='is_verified',
        ),
        migrations.RemoveField(
            model_name='twitterprofile',
            name='json',
        ),
        migrations.RemoveField(
            model_name='twitterprofile',
            name='listed_count',
        ),
        migrations.RemoveField(
            model_name='twitterprofile',
            name='location',
        ),
        migrations.RemoveField(
            model_name='twitterprofile',
            name='name',
        ),
        migrations.RemoveField(
            model_name='twitterprofile',
            name='profile_image_url',
        ),
        migrations.RemoveField(
            model_name='twitterprofile',
            name='status',
        ),
        migrations.RemoveField(
            model_name='twitterprofile',
            name='statuses_count',
        ),
        migrations.RemoveField(
            model_name='twitterprofile',
            name='urls',
        ),
    ]