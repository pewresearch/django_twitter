# Generated by Django 3.1.2 on 2021-06-17 13:50

from django.conf import settings
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import simple_history.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=250)),
            ],
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=250)),
            ],
        ),
        migrations.CreateModel(
            name='Tweet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('twitter_id', models.CharField(db_index=True, help_text="The object's unique Twitter ID", max_length=150, unique=True)),
                ('last_update_time', models.DateTimeField(auto_now=True, help_text='Last time the object was updated')),
                ('historical', models.BooleanField(default=False, help_text='Empty flag that you can use to track historical accounts')),
                ('created_at', models.DateTimeField(help_text='The time/date that the tweet was published', null=True)),
                ('links', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=400), help_text='Links contained in the tweet', null=True, size=None)),
                ('media', django.contrib.postgres.fields.ArrayField(base_field=models.JSONField(null=True), help_text='Media contained in the tweet', null=True, size=None)),
                ('text', models.CharField(help_text='Text extracted from the tweet, including expanded text and text from tweets that it quoted or retweeted (hence why the max length is longer than the twitter size limit', max_length=1500, null=True)),
                ('profile_mentions_raw', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=280), default=list, help_text='A list of profile screen names that were mentioned in the tweet', null=True, size=None)),
                ('language', models.CharField(help_text="The tweet's language", max_length=255, null=True)),
                ('retweet_count', models.IntegerField(help_text="Number of times the tweet was retweeted. Note: for tweets that are retweets (but not quote tweets), this count reflects the _original_ tweet's retweets, not just the retweeted version's retweets. When someone retweets a retweet that didn't have any additional commentary, that retweet gets redirected back to the original tweet.", null=True)),
                ('favorite_count', models.IntegerField(help_text="Number of times the tweet was favorited. Note: for tweets that are retweets (but not quote tweets), this count reflects the _original_ tweet's favorites, not just the retweeted version's favorites. When someone favorites a retweet that didn't have any additional commentary, that favorite gets redirected back to the original tweet.", null=True)),
                ('json', models.JSONField(default=dict, help_text='The raw JSON for the tweet', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TwitterHashtag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=150, unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TwitterProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('twitter_id', models.CharField(db_index=True, help_text="The object's unique Twitter ID", max_length=150, unique=True)),
                ('last_update_time', models.DateTimeField(auto_now=True, help_text='Last time the object was updated')),
                ('historical', models.BooleanField(default=False, help_text='Empty flag that you can use to track historical accounts')),
                ('tweet_backfilled', models.BooleanField(default=False, help_text="An indicator used in the `django_twitter_get_profile` command; True indicates that the profile's         tweet history has been backfilled as far as possible, so the sync function will stop after it hits an existing         tweet the next time it runs, unless you override this behavior.")),
                ('screen_name', models.CharField(db_index=True, help_text="The profile's screen name", max_length=100, null=True)),
                ('created_at', models.DateTimeField(help_text='When the profile was created', null=True)),
                ('twitter_error_code', models.IntegerField(help_text="The latest error code encountered when attempting to collect this profile's data from the API", null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TwitterProfileSnapshot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True, help_text='Timestamp indicating when the snapshot was saved')),
                ('screen_name', models.CharField(db_index=True, help_text="The profile's screen name", max_length=100, null=True)),
                ('name', models.CharField(help_text='The name of the profile', max_length=200, null=True)),
                ('contributors_enabled', models.BooleanField(help_text='Whether or not the profile allows contributors', null=True)),
                ('description', models.TextField(help_text="The profile's description/bio", null=True)),
                ('favorites_count', models.IntegerField(help_text='Number of favorited tweets', null=True)),
                ('followers_count', models.IntegerField(help_text='Number of followers', null=True)),
                ('followings_count', models.IntegerField(help_text="Number of accounts the profile follows ('followings')", null=True)),
                ('is_verified', models.BooleanField(help_text='Whether or not the profile is verified', null=True)),
                ('is_protected', models.BooleanField(help_text='Whether or not the profile is protected', null=True)),
                ('listed_count', models.IntegerField(null=True)),
                ('profile_image_url', models.TextField(help_text="URL to the profile's picture", null=True)),
                ('status', models.TextField(help_text="The profile's current status", null=True)),
                ('statuses_count', models.IntegerField(help_text='Number of tweets the profile has produced', null=True)),
                ('urls', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=300), default=list, help_text="A list of URLs contained in the profile's bio", size=None)),
                ('location', models.CharField(help_text="The profile's self-reported location", max_length=512, null=True)),
                ('json', models.JSONField(default=dict, help_text='The raw JSON for the profile at the time the snapshot was collected', null=True)),
                ('profile', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='snapshots', to='testapp.twitterprofile')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TwitterProfileSet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='A unique name associated with a set of profiles', max_length=256, unique=True)),
                ('profiles', models.ManyToManyField(related_name='twitter_profile_sets', to='testapp.TwitterProfile')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='twitterprofile',
            name='most_recent_snapshot',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='testapp.twitterprofilesnapshot'),
        ),
        migrations.AddField(
            model_name='twitterprofile',
            name='organization',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='twitter_profiles', to='testapp.organization'),
        ),
        migrations.AddField(
            model_name='twitterprofile',
            name='person',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='twitter_profiles', to='testapp.person'),
        ),
        migrations.CreateModel(
            name='TwitterFollowingList',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.DateTimeField(auto_now_add=True)),
                ('finish_time', models.DateTimeField(null=True)),
                ('followings', models.ManyToManyField(to='testapp.TwitterProfile')),
                ('profile', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='following_lists', to='testapp.twitterprofile')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TwitterFollowerList',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.DateTimeField(auto_now_add=True)),
                ('finish_time', models.DateTimeField(null=True)),
                ('followers', models.ManyToManyField(to='testapp.TwitterProfile')),
                ('profile', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='follower_lists', to='testapp.twitterprofile')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TweetSet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='A unique name associated with a set of tweets', max_length=256, unique=True)),
                ('tweets', models.ManyToManyField(related_name='tweet_sets', to='testapp.Tweet')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='tweet',
            name='hashtags',
            field=models.ManyToManyField(related_name='tweets', to='testapp.TwitterHashtag'),
        ),
        migrations.AddField(
            model_name='tweet',
            name='in_reply_to_status',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='replies', to='testapp.tweet'),
        ),
        migrations.AddField(
            model_name='tweet',
            name='profile',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='tweets', to='testapp.twitterprofile'),
        ),
        migrations.AddField(
            model_name='tweet',
            name='profile_mentions',
            field=models.ManyToManyField(related_name='tweet_mentions', to='testapp.TwitterProfile'),
        ),
        migrations.AddField(
            model_name='tweet',
            name='quoted_status',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='quotes', to='testapp.tweet'),
        ),
        migrations.AddField(
            model_name='tweet',
            name='retweeted_status',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='retweets', to='testapp.tweet'),
        ),
        migrations.CreateModel(
            name='HistoricalTwitterProfile',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('twitter_id', models.CharField(db_index=True, help_text="The object's unique Twitter ID", max_length=150)),
                ('last_update_time', models.DateTimeField(blank=True, editable=False, help_text='Last time the object was updated')),
                ('historical', models.BooleanField(default=False, help_text='Empty flag that you can use to track historical accounts')),
                ('tweet_backfilled', models.BooleanField(default=False, help_text="An indicator used in the `django_twitter_get_profile` command; True indicates that the profile's         tweet history has been backfilled as far as possible, so the sync function will stop after it hits an existing         tweet the next time it runs, unless you override this behavior.")),
                ('screen_name', models.CharField(db_index=True, help_text="The profile's screen name", max_length=100, null=True)),
                ('created_at', models.DateTimeField(help_text='When the profile was created', null=True)),
                ('twitter_error_code', models.IntegerField(help_text="The latest error code encountered when attempting to collect this profile's data from the API", null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('most_recent_snapshot', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='testapp.twitterprofilesnapshot')),
                ('organization', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='testapp.organization')),
                ('person', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='testapp.person')),
            ],
            options={
                'verbose_name': 'historical twitter profile',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalTweet',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('twitter_id', models.CharField(db_index=True, help_text="The object's unique Twitter ID", max_length=150)),
                ('last_update_time', models.DateTimeField(blank=True, editable=False, help_text='Last time the object was updated')),
                ('historical', models.BooleanField(default=False, help_text='Empty flag that you can use to track historical accounts')),
                ('created_at', models.DateTimeField(help_text='The time/date that the tweet was published', null=True)),
                ('links', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=400), help_text='Links contained in the tweet', null=True, size=None)),
                ('media', django.contrib.postgres.fields.ArrayField(base_field=models.JSONField(null=True), help_text='Media contained in the tweet', null=True, size=None)),
                ('text', models.CharField(help_text='Text extracted from the tweet, including expanded text and text from tweets that it quoted or retweeted (hence why the max length is longer than the twitter size limit', max_length=1500, null=True)),
                ('profile_mentions_raw', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=280), default=list, help_text='A list of profile screen names that were mentioned in the tweet', null=True, size=None)),
                ('language', models.CharField(help_text="The tweet's language", max_length=255, null=True)),
                ('retweet_count', models.IntegerField(help_text="Number of times the tweet was retweeted. Note: for tweets that are retweets (but not quote tweets), this count reflects the _original_ tweet's retweets, not just the retweeted version's retweets. When someone retweets a retweet that didn't have any additional commentary, that retweet gets redirected back to the original tweet.", null=True)),
                ('favorite_count', models.IntegerField(help_text="Number of times the tweet was favorited. Note: for tweets that are retweets (but not quote tweets), this count reflects the _original_ tweet's favorites, not just the retweeted version's favorites. When someone favorites a retweet that didn't have any additional commentary, that favorite gets redirected back to the original tweet.", null=True)),
                ('json', models.JSONField(default=dict, help_text='The raw JSON for the tweet', null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('in_reply_to_status', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='testapp.tweet')),
                ('profile', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='testapp.twitterprofile')),
                ('quoted_status', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='testapp.tweet')),
                ('retweeted_status', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='testapp.tweet')),
            ],
            options={
                'verbose_name': 'historical tweet',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
