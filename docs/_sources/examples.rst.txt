*************************************
Examples
*************************************

Django Twitter is designed to make it easy to collect and store data
from Twitter in a database, using Django. It is layered on top of
Pewhooks - our collection of Python utilities for interfacing with
various APIs, including Twitter - and provides a set of standardized
abstract Django models and Django commands for querying the Twitter API
and storing the data you get back.

Configuration
-------------

In the following examples, we have a test app set up that has Django
Twitter installed like so:

settings.py
~~~~~~~~~~~

.. code:: python

   INSTALLED_APPS = [
       "django.contrib.auth",
       "django.contrib.contenttypes",
       "django.contrib.sites",
       "django_twitter",
       "testapp",
   ]
   TWITTER_APP = "testapp"

And in our app’s ``models.py`` file, we import all of the abstract
models that Django Twitter provides, and create them as concrete models
in our own app. The abstract models define a “template” for how to store
Twitter data, but the tables will be created for and belong to our own
app. You’ll also notice that we have two other tables in our app -
``Person`` and ``Organization``. What’s nice about Django Twitter
providing *abstract* models is that you can build on the model templates
and extend them with additional data however you like. In our app, we’re
going to add some additional metadata on who owns each Twitter account,
and store that info in other custom tables in our app.

models.py
~~~~~~~~~

.. code:: python

   from django.db import models
   from django_twitter.models import *

   class Person(models.Model):
       name = models.CharField(max_length=250)
       
   class Organization(models.Model):
       name = models.CharField(max_length=250)

   class TwitterProfile(AbstractTwitterProfile):

       person = models.ForeignKey(
           "testapp.Person",
           related_name="twitter_profiles",
           null=True,
           on_delete=models.SET_NULL,
       )
       organization = models.ForeignKey(
           "testapp.Organization",
           related_name="twitter_profiles",
           null=True,
           on_delete=models.SET_NULL,
       )

   class TwitterProfileSnapshot(AbstractTwitterProfileSnapshot):
       pass

   class Tweet(AbstractTweet):
       pass

   class TwitterFollowerList(AbstractTwitterFollowerList):
       pass

   class TwitterFollowingList(AbstractTwitterFollowingList):
       pass

   class TwitterHashtag(AbstractTwitterHashtag):
       pass

   class TwitterPlace(AbstractTwitterPlace):
       pass

   class TweetSet(AbstractTweetSet):
       pass

   class TwitterProfileSet(AbstractTwitterProfileSet):
       pass

Finally, we’re going to grab our Twitter credentials and save them as
environment variables. Django Twitter allows you to manually pass your
Twitter credentials to all of its data collection commands, but it’s
much easier to take advantage of Pewhooks’ support for environment
variables and let it fetch them automatically. The variables it needs
are ``TWITTER_API_KEY``, ``TWITTER_API_SECRET``,
``TWITTER_API_ACCESS_TOKEN``, ``TWITTER_API_ACCESS_SECRET``.

With our credentials set and the above two files figured out, we’ve now
got Django Twitter all configured. We just need to run
``python manage.py makemigrations testapp`` and
``python manage.py migrate`` to actually create the tables, and then
we’re ready to load in some data! Below is the list of accounts we’re
going to track.

Adding accounts and downloading profile data
--------------------------------------------

.. code:: ipython3

    MY_ACCOUNTS = [
        "pewresearch",
        "pewglobal",
        "pewmethods",
        "pewjournalism",
        "facttank",
        "pewscience",
        "pewreligion",
        "pewhispanic",
        "pewinternet",
        "pvankessel",
        "justinbieber",
    ]

Django Twitter provides a bunch of built-in management commands that
make it easy to collect Twitter data. If we wanted to start pulling in
data for these profiles, we could run the following command from the CLI
and Django Twitter would hit the API and store the results in the
database:

``python manage.py django_twitter_get_profile pewresearch``

But Django also provides a ``call_command`` function that lets you call
management commands programatically, so that’s what we’re going to use
here.

.. code:: ipython3

    from django.core.management import call_command

.. code:: ipython3

    for handle in MY_ACCOUNTS:
        call_command(
            "django_twitter_get_profile", handle
        )


.. parsed-literal::

    Collecting profile data for pewresearch
    Successfully saved profile data for pewresearch: http://twitter.com/pewresearch
    Collecting profile data for pewglobal
    Successfully saved profile data for pewglobal: http://twitter.com/pewglobal
    Collecting profile data for pewmethods
    Successfully saved profile data for pewmethods: http://twitter.com/pewmethods
    Collecting profile data for pewjournalism
    Successfully saved profile data for pewjournalism: http://twitter.com/pewjournalism
    Collecting profile data for facttank
    Successfully saved profile data for facttank: http://twitter.com/facttank
    Collecting profile data for pewscience
    Successfully saved profile data for pewscience: http://twitter.com/pewscience
    Collecting profile data for pewreligion
    Successfully saved profile data for pewreligion: http://twitter.com/pewreligion
    Collecting profile data for pewhispanic
    Successfully saved profile data for pewhispanic: http://twitter.com/pewhispanic
    Collecting profile data for pewinternet
    Successfully saved profile data for pewinternet: http://twitter.com/pewinternet
    Collecting profile data for pvankessel
    Successfully saved profile data for pvankessel: http://twitter.com/pvankessel
    Collecting profile data for justinbieber
    Successfully saved profile data for justinbieber: http://twitter.com/justinbieber


.. code:: ipython3

    from testapp.models import TwitterProfile
    TwitterProfile.objects.count()




.. parsed-literal::

    11



.. code:: ipython3

    TwitterProfile.objects.filter(screen_name='pewresearch').values()




.. parsed-literal::

    <QuerySet [{'id': 1, 'twitter_id': '22642788', 'last_update_time': datetime.datetime(2021, 6, 15, 14, 26, 47, 830012), 'historical': False, 'tweet_backfilled': False, 'screen_name': 'pewresearch', 'created_at': datetime.datetime(2009, 3, 3, 10, 39, 39), 'twitter_error_code': None, 'person_id': None, 'organization_id': None, 'most_recent_snapshot_id': 1}]>



Hmm, that looks like we’ve got less data than we expected. Where’d all
the data go? Well, because Twitter profiles change over time - people
gain and lose followers, they change their descriptions (and sometimes
even their screen names) - and because we might be interested in
tracking that data, Django Twitter actually stores profile data in a
separate table, every time it queries the API. We call these “profile
snapshots” and you can access them like so:

.. code:: ipython3

    profile = TwitterProfile.objects.get(screen_name='pewresearch')
    profile.snapshots.all()




.. parsed-literal::

    <QuerySet [<TwitterProfileSnapshot: pewresearch: http://twitter.com/pewresearch AS OF 2021-06-15 14:26:47.799024>]>



.. code:: ipython3

    profile.snapshots.values()




.. parsed-literal::

    <QuerySet [{'id': 1, 'twitter_id': '', 'last_update_time': datetime.datetime(2021, 6, 15, 14, 26, 47, 817208), 'historical': False, 'timestamp': datetime.datetime(2021, 6, 15, 14, 26, 47, 799024), 'screen_name': 'pewresearch', 'name': 'Pew Research Center', 'contributors_enabled': False, 'description': 'Nonpartisan, non-advocacy data and analysis on the issues, attitudes and trends shaping the world. Subscribe: https://t.co/Kpq1V0w9bM ✉️', 'favorites_count': 892, 'followers_count': 430625, 'followings_count': 96, 'is_verified': True, 'is_protected': False, 'listed_count': 13195, 'profile_image_url': 'http://pbs.twimg.com/profile_images/879728447026868228/U4Uzpdp6_normal.jpg', 'status': '@Katrina_HRM You might also enjoy our short email mini-course on the U.S. Census authored by @allthingscensus. Less… https://t.co/hJrYbltDWh', 'statuses_count': 90347, 'urls': ['https://www.pewresearch.org/'], 'location': 'Washington, DC', 'json': {'id': 22642788, 'url': 'https://t.co/OBLpll8VR0', 'lang': None, 'name': 'Pew Research Center', 'id_str': '22642788', 'status': {'id': 1404865073684828161, 'geo': None, 'lang': 'en', 'text': '@Katrina_HRM You might also enjoy our short email mini-course on the U.S. Census authored by @allthingscensus. Less… https://t.co/hJrYbltDWh', 'place': None, 'id_str': '1404865073684828161', 'source': '<a href="https://about.twitter.com/products/tweetdeck" rel="nofollow">TweetDeck</a>', 'entities': {'urls': [{'url': 'https://t.co/hJrYbltDWh', 'indices': [117, 140], 'display_url': 'twitter.com/i/web/status/1…', 'expanded_url': 'https://twitter.com/i/web/status/1404865073684828161'}], 'symbols': [], 'hashtags': [], 'user_mentions': [{'id': 77834136, 'name': 'Katrina Jones', 'id_str': '77834136', 'indices': [0, 12], 'screen_name': 'Katrina_HRM'}, {'id': 356872253, 'name': 'All Things Census', 'id_str': '356872253', 'indices': [93, 109], 'screen_name': 'allthingscensus'}]}, 'favorited': False, 'retweeted': False, 'truncated': True, 'created_at': 'Tue Jun 15 18:15:09 +0000 2021', 'coordinates': None, 'contributors': None, 'retweet_count': 1, 'favorite_count': 2, 'is_quote_status': False, 'possibly_sensitive': False, 'in_reply_to_user_id': 77834136, 'in_reply_to_status_id': 1404850695715659777, 'in_reply_to_screen_name': 'Katrina_HRM', 'in_reply_to_user_id_str': '77834136', 'in_reply_to_status_id_str': '1404850695715659777'}, 'entities': {'url': {'urls': [{'url': 'https://t.co/OBLpll8VR0', 'indices': [0, 23], 'display_url': 'pewresearch.org', 'expanded_url': 'https://www.pewresearch.org/'}]}, 'description': {'urls': [{'url': 'https://t.co/Kpq1V0w9bM', 'indices': [110, 133], 'display_url': 'pewresearch.org/follow-us/', 'expanded_url': 'https://www.pewresearch.org/follow-us/'}]}}, 'location': 'Washington, DC', 'verified': True, 'following': False, 'protected': False, 'time_zone': None, 'created_at': 'Tue Mar 03 16:39:39 +0000 2009', 'utc_offset': None, 'description': 'Nonpartisan, non-advocacy data and analysis on the issues, attitudes and trends shaping the world. Subscribe: https://t.co/Kpq1V0w9bM ✉️', 'geo_enabled': True, 'screen_name': 'pewresearch', 'listed_count': 13195, 'friends_count': 96, 'is_translator': False, 'notifications': False, 'statuses_count': 90347, 'default_profile': False, 'followers_count': 430625, 'translator_type': 'none', 'favourites_count': 892, 'profile_location': None, 'profile_image_url': 'http://pbs.twimg.com/profile_images/879728447026868228/U4Uzpdp6_normal.jpg', 'profile_banner_url': 'https://pbs.twimg.com/profile_banners/22642788/1494338667', 'profile_link_color': '0083B3', 'profile_text_color': '525151', 'follow_request_sent': False, 'contributors_enabled': False, 'has_extended_profile': False, 'default_profile_image': False, 'withheld_in_countries': [], 'is_translation_enabled': False, 'profile_background_tile': True, 'profile_image_url_https': 'https://pbs.twimg.com/profile_images/879728447026868228/U4Uzpdp6_normal.jpg', 'profile_background_color': 'EFEFEF', 'profile_sidebar_fill_color': 'DBE7ED', 'profile_background_image_url': 'http://abs.twimg.com/images/themes/theme1/bg.png', 'profile_sidebar_border_color': 'DBE7ED', 'profile_use_background_image': False, 'profile_background_image_url_https': 'https://abs.twimg.com/images/themes/theme1/bg.png'}, 'profile_id': 1}]>



There’s the data! For convenience, you can always access the most recent
snapshot of a profile directly using the ``most_recent_snapshot`` field:

.. code:: ipython3

    profile.most_recent_snapshot




.. parsed-literal::

    <TwitterProfileSnapshot: pewresearch: http://twitter.com/pewresearch AS OF 2021-06-15 14:26:47.799024>



Collecting tweets
-----------------

Okay, now let’s get some tweets using the
``django_twitter_get_profile_tweets`` command. The Twitter v1 API allows
you to go back as far as the ~3200 most recent tweets produced by an
account. With query limits, that would take a while, so we’re going to
set a limit of 25 tweets. But normally, we’d probably want to grab
everything we could, and then periodically run this command again to get
new tweets on a regular basis. Our Twitter account is pretty active -
but it’s definitely not producing 3200 tweets every day, so when we run
this command a second time, we probably don’t need to iterate through
everything all over again. Instead, Django Twitter sets a
``tweet_backfilled=True`` flag on the profile the first time it works
its way through the full available feed for a profile. Then, in
subsequent runs of ``django_twitter_get_profile_tweets``, it’ll default
to breaking off the data collection when it encounters a tweet it’s
already seen.

(Sidenote: since you’re probably collecting tweets for multiple profiles
and it’s possible that some accounts mention or retweet each other,
Django Twitter is smart enough to check for this, and it only breaks off
when it encounters a tweet that could only have been captured by
collecting the profile’s own feed.)

You can ignore the backfill flag by simply passing ``--ignore_backfill``
to the command, and it’ll keep iterating. And, if you just want to
ignore the backfill flag for a limited timeframe (only refreshing
existing tweets up to a certain point) then you can easily pass
``--max_backfill_days`` or ``--max_backfill_date`` to the command to
tell it how far back you want to go. Finally, Django Twitter avoids
overwriting existing tweet data, unless you pass ``--overwrite``.
Combining some of these flags - like
``--ignore_backfill --max_backfill_days 7 --overwrite`` - can be useful
if you want to refresh the stats (i.e. likes, retweets) for recent
tweets, but don’t care after a certain point (stats tend to level-off
after a few days, so we often stop refreshing tweets after a week).

Anyway, below, we’re going to collected the most recent 25 tweets for
the @pewresearch account:

.. code:: ipython3

    call_command(
        "django_twitter_get_profile_tweets",
        "pewresearch",
        limit=25
    )


.. parsed-literal::

    Retrieving tweets for user pewresearch: 0it [00:00, ?it/s]
    Retrieving tweets for user pewresearch
    Retrieving tweets for user pewresearch: 24it [00:02,  8.70it/s]
    pewresearch: http://twitter.com/pewresearch: 25 tweets scanned, 25 updated


.. code:: ipython3

    from testapp.models import Tweet
    Tweet.objects.count()




.. parsed-literal::

    35



.. code:: ipython3

    TwitterProfile.objects.count()




.. parsed-literal::

    19



Awesome, we’ve got tweets now! But wait, we have more tweets than we
expected, and we also have more Twitter profiles. What gives?

Well, Django Twitter automatically creates new records for any and all
tweets and accounts it encounters. So, if @pewresearch quote tweets an
account we hadn’t seen before, both the quote tweet and the original
tweet get created in the database, along with the account that created
the quoted tweet. This is nice, because our lovely database grows and
tracks all of the data it can - but now we’ve got extra profiles. Which
ones are our original ones?

We could just keep using our initial list of screen names to keep track
of our “primary” accounts, but that poses another problem: screen names
can change and get recycled by new accounts. If we were to retire our
@pewresearch account and it were to get snatched up by a spam bot (not
an uncommon scenario for popular handles), our queries would start
pulling in spammy tweets, and we wouldn’t even know something was wrong
unless we took a close look. The better way of tracking accounts is to
use their actually-unique Twitter IDs, which you get back from the API
the first time you query a screen name.

.. code:: ipython3

    profile.twitter_id




.. parsed-literal::

    '22642788'



So now we have to go and look up all of our accounts’ *actual* IDs and
replace our list of screen names? That’s a huge pain! Wouldn’t it be
nice if we could just define lists of accounts that we care about
directly in the database?

Profile and tweet sets
----------------------

That’s where profile and tweet sets come in. Every Django Twitter
command (where it makes sense) accepts ``--add_to_profile_set`` and/or
``--add_to_tweet_set`` commands that take arbitrary labels that get
associated with the profiles and/or tweets that it encounters. This
makes it really easy to give a set of profiles or tweets a name, and
then you can access that set directly in the database - and better yet,
you can also run commands directly on a *set* of profiles all at once.
Let’s see how that works.

Let’s repeat the process of looping over and loading in our accounts,
but this time we’re going to add them to a profile set.

.. code:: ipython3

    for handle in MY_ACCOUNTS:
        call_command(
            "django_twitter_get_profile", handle, add_to_profile_set="my_profile_set"
        )


.. parsed-literal::

    Collecting profile data for pewresearch
    Successfully saved profile data for pewresearch: http://twitter.com/pewresearch
    Collecting profile data for pewglobal
    Successfully saved profile data for pewglobal: http://twitter.com/pewglobal
    Collecting profile data for pewmethods
    Successfully saved profile data for pewmethods: http://twitter.com/pewmethods
    Collecting profile data for pewjournalism
    Successfully saved profile data for pewjournalism: http://twitter.com/pewjournalism
    Collecting profile data for facttank
    Successfully saved profile data for facttank: http://twitter.com/facttank
    Collecting profile data for pewscience
    Successfully saved profile data for pewscience: http://twitter.com/pewscience
    Collecting profile data for pewreligion
    Successfully saved profile data for pewreligion: http://twitter.com/pewreligion
    Collecting profile data for pewhispanic
    Successfully saved profile data for pewhispanic: http://twitter.com/pewhispanic
    Collecting profile data for pewinternet
    Successfully saved profile data for pewinternet: http://twitter.com/pewinternet
    Collecting profile data for pvankessel
    Successfully saved profile data for pvankessel: http://twitter.com/pvankessel
    Collecting profile data for justinbieber
    Successfully saved profile data for justinbieber: http://twitter.com/justinbieber


Now we can access these accounts through the profile set that we just
created:

.. code:: ipython3

    from testapp.models import TwitterProfileSet
    
    TwitterProfileSet.objects.get(name="my_profile_set").profiles.count()




.. parsed-literal::

    11



Now, the next time we want to refresh the profile data for these
accounts, we can do it all at once by using the
``django_twitter_get_profile_set`` command, no for-loop necessary - and
no need to specify those problematic screen names; Django Twitter will
use the correct unique IDs automatically:

.. code:: ipython3

    call_command(
        "django_twitter_get_profile_set", "my_profile_set"
    )


.. parsed-literal::

      0%|          | 0/11 [00:00<?, ?it/s]
    Collecting profile data for 1265726480
    Successfully saved profile data for facttank: http://twitter.com/facttank
      9%|▉         | 1/11 [00:00<00:03,  3.17it/s]
    Collecting profile data for 1262729180
    Successfully saved profile data for pewscience: http://twitter.com/pewscience
     18%|█▊        | 2/11 [00:00<00:02,  3.50it/s]
    Collecting profile data for 36462231
    Successfully saved profile data for pewreligion: http://twitter.com/pewreligion
     27%|██▋       | 3/11 [00:00<00:02,  3.25it/s]
    Collecting profile data for 426041590
    Successfully saved profile data for pewhispanic: http://twitter.com/pewhispanic
     36%|███▋      | 4/11 [00:01<00:02,  2.98it/s]
    Collecting profile data for 22642788
    Successfully saved profile data for pewresearch: http://twitter.com/pewresearch
     45%|████▌     | 5/11 [00:01<00:01,  3.16it/s]
    Collecting profile data for 831470472
    Successfully saved profile data for pewglobal: http://twitter.com/pewglobal
     55%|█████▍    | 6/11 [00:01<00:01,  3.48it/s]
    Collecting profile data for 3015897974
    Successfully saved profile data for pewmethods: http://twitter.com/pewmethods
     64%|██████▎   | 7/11 [00:02<00:01,  3.74it/s]
    Collecting profile data for 111339670
    Successfully saved profile data for pewjournalism: http://twitter.com/pewjournalism
     73%|███████▎  | 8/11 [00:02<00:00,  3.68it/s]
    Collecting profile data for 17071048
    Successfully saved profile data for pewinternet: http://twitter.com/pewinternet
     82%|████████▏ | 9/11 [00:02<00:00,  3.70it/s]
    Collecting profile data for 530977797
    Successfully saved profile data for pvankessel: http://twitter.com/pvankessel
     91%|█████████ | 10/11 [00:02<00:00,  3.27it/s]
    Collecting profile data for 27260086
    Successfully saved profile data for justinbieber: http://twitter.com/justinbieber
    100%|██████████| 11/11 [00:03<00:00,  3.32it/s]


And to download the latest tweets for *all* of these accounts, we can
now run the ``django_twitter_get_profile_set_tweets`` command

.. code:: ipython3

    call_command(
        "django_twitter_get_profile_set_tweets",
        "my_profile_set",
        limit=25,
        overwrite=True,
        ignore_backfill=True
    )


.. parsed-literal::

    Retrieving tweets for user facttank: 0it [00:00, ?it/s]
    Retrieving tweets for user facttank
    Retrieving tweets for user facttank: 24it [00:02, 11.20it/s]
    facttank: http://twitter.com/facttank: 25 tweets scanned, 25 updated
    Retrieving tweets for user pewscience: 0it [00:00, ?it/s]
    Retrieving tweets for user pewscience
    Retrieving tweets for user pewscience: 24it [00:02,  9.66it/s]
    pewscience: http://twitter.com/pewscience: 25 tweets scanned, 25 updated
    Retrieving tweets for user pewreligion: 0it [00:00, ?it/s]
    Retrieving tweets for user pewreligion
    Retrieving tweets for user pewreligion: 24it [00:02, 11.89it/s]
    pewreligion: http://twitter.com/pewreligion: 25 tweets scanned, 25 updated
    Retrieving tweets for user pewhispanic: 0it [00:00, ?it/s]
    Retrieving tweets for user pewhispanic
    Retrieving tweets for user pewhispanic: 24it [00:02,  8.59it/s]
    pewhispanic: http://twitter.com/pewhispanic: 25 tweets scanned, 25 updated
    Retrieving tweets for user pewresearch: 0it [00:00, ?it/s]
    Retrieving tweets for user pewresearch
    Retrieving tweets for user pewresearch: 24it [00:02, 11.24it/s]
    pewresearch: http://twitter.com/pewresearch: 25 tweets scanned, 25 updated
    Retrieving tweets for user pewglobal: 0it [00:00, ?it/s]
    Retrieving tweets for user pewglobal
    Retrieving tweets for user pewglobal: 24it [00:02, 11.29it/s]
    pewglobal: http://twitter.com/pewglobal: 25 tweets scanned, 25 updated
    Retrieving tweets for user pewmethods: 0it [00:00, ?it/s]
    Retrieving tweets for user pewmethods
    Retrieving tweets for user pewmethods: 24it [00:02,  8.53it/s]
    pewmethods: http://twitter.com/pewmethods: 25 tweets scanned, 25 updated
    Retrieving tweets for user pewjournalism: 0it [00:00, ?it/s]
    Retrieving tweets for user pewjournalism
    Retrieving tweets for user pewjournalism: 24it [00:01, 13.64it/s]
    pewjournalism: http://twitter.com/pewjournalism: 25 tweets scanned, 25 updated
    Retrieving tweets for user pewinternet: 0it [00:00, ?it/s]
    Retrieving tweets for user pewinternet
    Retrieving tweets for user pewinternet: 24it [00:02, 11.88it/s]
    pewinternet: http://twitter.com/pewinternet: 25 tweets scanned, 25 updated
    Retrieving tweets for user pvankessel: 0it [00:00, ?it/s]
    Retrieving tweets for user pvankessel
    Retrieving tweets for user pvankessel: 24it [00:02,  9.78it/s]
    pvankessel: http://twitter.com/pvankessel: 25 tweets scanned, 25 updated
    Retrieving tweets for user justinbieber: 0it [00:00, ?it/s]
    Retrieving tweets for user justinbieber
    Retrieving tweets for user justinbieber: 24it [00:03,  7.96it/s]
    justinbieber: http://twitter.com/justinbieber: 25 tweets scanned, 25 updated
    100%|██████████| 11/11 [00:29<00:00,  2.67s/it]


We can also keep track of all the tweets we collect when we run this
command, by passing it a label for a tweet set:

.. code:: ipython3

    call_command(
        "django_twitter_get_profile_set_tweets",
        "my_profile_set",
        limit=25,
        overwrite=True,
        ignore_backfill=True,
        add_to_tweet_set="my_tweet_set"
    )


.. parsed-literal::

    Retrieving tweets for user pewscience: 0it [00:00, ?it/s]
    Retrieving tweets for user pewscience
    Retrieving tweets for user pewscience: 24it [00:02, 11.05it/s]
    pewscience: http://twitter.com/pewscience: 25 tweets scanned, 25 updated
    Retrieving tweets for user pewreligion: 0it [00:00, ?it/s]
    Retrieving tweets for user pewreligion
    Retrieving tweets for user pewreligion: 24it [00:02, 10.83it/s]
    pewreligion: http://twitter.com/pewreligion: 25 tweets scanned, 25 updated
    Retrieving tweets for user facttank: 0it [00:00, ?it/s]
    Retrieving tweets for user facttank
    Retrieving tweets for user facttank: 24it [00:01, 13.98it/s]
    facttank: http://twitter.com/facttank: 25 tweets scanned, 25 updated
    Retrieving tweets for user pewhispanic: 0it [00:00, ?it/s]
    Retrieving tweets for user pewhispanic
    Retrieving tweets for user pewhispanic: 24it [00:02,  8.88it/s]
    pewhispanic: http://twitter.com/pewhispanic: 25 tweets scanned, 25 updated
    Retrieving tweets for user pewglobal: 0it [00:00, ?it/s]
    Retrieving tweets for user pewglobal
    Retrieving tweets for user pewglobal: 24it [00:01, 12.44it/s]
    pewglobal: http://twitter.com/pewglobal: 25 tweets scanned, 25 updated
    Retrieving tweets for user pewmethods: 0it [00:00, ?it/s]
    Retrieving tweets for user pewmethods
    Retrieving tweets for user pewmethods: 24it [00:02, 10.44it/s]
    pewmethods: http://twitter.com/pewmethods: 25 tweets scanned, 25 updated
    Retrieving tweets for user pewjournalism: 0it [00:00, ?it/s]
    Retrieving tweets for user pewjournalism
    Retrieving tweets for user pewjournalism: 24it [00:02, 10.42it/s]
    pewjournalism: http://twitter.com/pewjournalism: 25 tweets scanned, 25 updated
    Retrieving tweets for user pewinternet: 0it [00:00, ?it/s]
    Retrieving tweets for user pewinternet
    Retrieving tweets for user pewinternet: 24it [00:02, 10.88it/s]
    pewinternet: http://twitter.com/pewinternet: 25 tweets scanned, 25 updated
    Retrieving tweets for user pewresearch: 0it [00:00, ?it/s]
    Retrieving tweets for user pewresearch
    Retrieving tweets for user pewresearch: 24it [00:02, 10.47it/s]
    pewresearch: http://twitter.com/pewresearch: 25 tweets scanned, 25 updated
    Retrieving tweets for user pvankessel: 0it [00:00, ?it/s]
    Retrieving tweets for user pvankessel
    Retrieving tweets for user pvankessel: 24it [00:02, 10.83it/s]
    pvankessel: http://twitter.com/pvankessel: 25 tweets scanned, 25 updated
    Retrieving tweets for user justinbieber: 0it [00:00, ?it/s]
    Retrieving tweets for user justinbieber
    Retrieving tweets for user justinbieber: 24it [00:02,  9.07it/s]
    justinbieber: http://twitter.com/justinbieber: 25 tweets scanned, 25 updated
    100%|██████████| 11/11 [00:28<00:00,  2.56s/it]


.. code:: ipython3

    from testapp.models import TweetSet
    TweetSet.objects.get(name="my_tweet_set").tweets.count()




.. parsed-literal::

    275



And we could even add those profiles to an entirely new profile set, to
keep track of data collection, for example.

.. code:: ipython3

    call_command(
        "django_twitter_get_profile_set_tweets",
        "my_profile_set",
        limit=25,
        overwrite=True,
        ignore_backfill=True,
        add_to_tweet_set="my_tweet_set",
        add_to_profile_set="my_second_profile_set",
    )

.. parsed-literal::

    Retrieving tweets for user pewreligion: 0it [00:00, ?it/s]
    Retrieving tweets for user pewreligion
    Retrieving tweets for user pewreligion: 24it [00:02,  9.12it/s]
    pewreligion: http://twitter.com/pewreligion: 25 tweets scanned, 25 updated
    Retrieving tweets for user facttank: 0it [00:00, ?it/s]
    Retrieving tweets for user facttank
    Retrieving tweets for user facttank: 24it [00:01, 13.87it/s]
    facttank: http://twitter.com/facttank: 25 tweets scanned, 25 updated
    Retrieving tweets for user pewhispanic: 0it [00:00, ?it/s]
    Retrieving tweets for user pewhispanic
    Retrieving tweets for user pewhispanic: 24it [00:02,  9.02it/s]
    pewhispanic: http://twitter.com/pewhispanic: 25 tweets scanned, 25 updated
    Retrieving tweets for user pewglobal: 0it [00:00, ?it/s]
    Retrieving tweets for user pewglobal
    Retrieving tweets for user pewglobal: 24it [00:01, 12.75it/s]
    pewglobal: http://twitter.com/pewglobal: 25 tweets scanned, 25 updated
    Retrieving tweets for user pewinternet: 0it [00:00, ?it/s]
    Retrieving tweets for user pewinternet
    Retrieving tweets for user pewinternet: 24it [00:02, 11.19it/s]
    pewinternet: http://twitter.com/pewinternet: 25 tweets scanned, 25 updated
    Retrieving tweets for user pewmethods: 0it [00:00, ?it/s]
    Retrieving tweets for user pewmethods
    Retrieving tweets for user pewmethods: 24it [00:02, 11.62it/s]
    pewmethods: http://twitter.com/pewmethods: 25 tweets scanned, 25 updated
    Retrieving tweets for user pewscience: 0it [00:00, ?it/s]
    Retrieving tweets for user pewscience
    Retrieving tweets for user pewscience: 24it [00:02,  9.99it/s]
    pewscience: http://twitter.com/pewscience: 25 tweets scanned, 25 updated
    Retrieving tweets for user pewjournalism: 0it [00:00, ?it/s]
    Retrieving tweets for user pewjournalism
    Retrieving tweets for user pewjournalism: 24it [00:01, 14.20it/s]
    pewjournalism: http://twitter.com/pewjournalism: 25 tweets scanned, 25 updated
    Retrieving tweets for user pewresearch: 0it [00:00, ?it/s]
    Retrieving tweets for user pewresearch
    Retrieving tweets for user pewresearch: 24it [00:02, 11.25it/s]
    pewresearch: http://twitter.com/pewresearch: 25 tweets scanned, 25 updated
    Retrieving tweets for user pvankessel: 0it [00:00, ?it/s]
    Retrieving tweets for user pvankessel
    Retrieving tweets for user pvankessel: 24it [00:02, 10.63it/s]
    pvankessel: http://twitter.com/pvankessel: 25 tweets scanned, 25 updated
    Retrieving tweets for user justinbieber: 0it [00:00, ?it/s]
    Retrieving tweets for user justinbieber
    Retrieving tweets for user justinbieber: 24it [00:02,  9.66it/s]
    justinbieber: http://twitter.com/justinbieber: 25 tweets scanned, 25 updated
    100%|██████████| 11/11 [00:27<00:00,  2.49s/it]


.. code:: ipython3

    TwitterProfileSet.objects.get(name="my_second_profile_set").profiles.count()




.. parsed-literal::

    11



Followers and followings lists
------------------------------

So that’s how to collect profile and tweet data, but you also might be
interested in tracking the followers or friends (we call them
“followings”) for particular accounts. For really popular accounts, not
only can it take a super long time to collect all of their followers
from the API, their followers can also change substantially over time.
To that end, Django Twitter stores lists of followers/followings in a
dedicated table, tracking the start and finish time of the data
collection, and storing each list separately every time you collect it.
Let’s see how that works.

.. code:: ipython3

    call_command("django_twitter_get_profile_followers", "pewresearch", limit=25)


.. parsed-literal::

    Retrieving followers for user pewresearch: 25it [00:00, 58.31it/s]


We now have a TwitterFollowerList object attached to our profile, and if
we take a look at its values in the table, we can see that it logged its
start and finish time (although we forced a limit of 25, so that’s a
little misleading!)

.. code:: ipython3

    pew = TwitterProfile.objects.get(screen_name="pewresearch")
    pew.follower_lists.all()




.. parsed-literal::

    <QuerySet [<TwitterFollowerList: TwitterFollowerList object (1)>]>



.. code:: ipython3

    pew.follower_lists.values()




.. parsed-literal::

    <QuerySet [{'id': 1, 'start_time': datetime.datetime(2021, 6, 15, 14, 28, 26, 447871), 'finish_time': datetime.datetime(2021, 6, 15, 14, 28, 26, 881229), 'profile_id': 1}]>



We can also use a shortcut function on TwitterProfile objects to grab
the most recent list

.. code:: ipython3

    pew.current_follower_list()




.. parsed-literal::

    <TwitterFollowerList: TwitterFollowerList object (1)>



And we can jump directly to the profile objects in that list directly
using another shortcut function:

.. code:: ipython3

    pew.current_followers()




.. parsed-literal::

    <QuerySet [<TwitterProfile: 1404793895838359552>, <TwitterProfile: 1207586894130769922>, <TwitterProfile: 1095705562480820224>, <TwitterProfile: 1296137977169494017>, <TwitterProfile: 422795601>, <TwitterProfile: 1352012895316537345>, <TwitterProfile: 1404860475590905857>, <TwitterProfile: 4764251969>, <TwitterProfile: 826425088975183873>, <TwitterProfile: 2230952041>, <TwitterProfile: 2274067960>, <TwitterProfile: 557234082>, <TwitterProfile: 1949288179>, <TwitterProfile: 2735032766>, <TwitterProfile: 1404812122094247944>, <TwitterProfile: 1355955487284502528>, <TwitterProfile: 1281699263639150593>, <TwitterProfile: 3362571939>, <TwitterProfile: 338711547>, <TwitterProfile: 756597997>, '...(remaining elements truncated)...']>



.. code:: ipython3

    pew.current_followers().count()




.. parsed-literal::

    25



But as you can see, we pretty much just have a list of Twitter IDs

.. code:: ipython3

    pew.current_followers().values()[0]




.. parsed-literal::

    {'id': 72,
     'twitter_id': '1404793895838359552',
     'last_update_time': datetime.datetime(2021, 6, 15, 14, 28, 26, 698450),
     'historical': False,
     'tweet_backfilled': False,
     'screen_name': None,
     'created_at': None,
     'twitter_error_code': None,
     'person_id': None,
     'organization_id': None,
     'most_recent_snapshot_id': None}



If we want to ask Twitter to actually provide us with profile info for
each follower, we have to specifically request it - because it eats up a
LOT more API quota. To request this data, you just need to pass
``--hydrate``

.. code:: ipython3

    call_command("django_twitter_get_profile_followers", "pewresearch", limit=25, hydrate=True)


.. parsed-literal::

    Retrieving followers for user pewresearch: 25it [00:01, 13.30it/s]


And now we have actual data, including screen names and profile
snapshots

.. code:: ipython3

    pew.current_followers().values()[0]




.. parsed-literal::

    {'id': 72,
     'twitter_id': '1404793895838359552',
     'last_update_time': datetime.datetime(2021, 6, 15, 14, 28, 28, 3262),
     'historical': False,
     'tweet_backfilled': False,
     'screen_name': 'garghiv',
     'created_at': datetime.datetime(2021, 6, 15, 8, 32, 36),
     'twitter_error_code': None,
     'person_id': None,
     'organization_id': None,
     'most_recent_snapshot_id': 1148}



So we can do fancy things like, see how many of @pewresearch’s followers
have at least 10 followers themselves

.. code:: ipython3

    pew.current_followers().filter(most_recent_snapshot__followers_count__gte=10).count()




.. parsed-literal::

    18



Followings works the exact same way - just substitute the word
“follower” for “following”

Data auditing utilities (looking for account and coverage errors)
-----------------------------------------------------------------

When you’re working with social media data, there can be a lot of moving
parts, and occasionally bad data can slip into your database. Maybe a
handle that you got from a third-party list was outdated, or someone
gave you a fake username that turned out to be a spam bot, or someone
that you’ve been tracking deleted their profile and it immediately got
picked up by a spam bot. There are ways to minimize the risk of all of
this happening, but there’s no substitute for doing manual spot-checks!
Fortunately, Django Twitter offers some utility functions to help you
check for weird accounts.

In ``django_twitter.utils`` there are two functions that take a set of
profiles and compute their average text similarity to each other by
looking at a sample of their recent tweets
(``identify_unusual_profiles_by_tweet_text``) or their profile
descriptions (``identify_unusual_profiles_by_descriptions``). Usually
we’re interested in tracking accounts that have something in common -
politicians, news organizations, celebrities and other public figures.
In some cases, it’s reasonable to assume that the accounts in our
collection will tweet similar content - or at least, their tweets will
be more similar to each other than the tweets produced by a spam bot.

In our example, it turns out that Justin Bieber’s tweets are so reliably
different than the content produced by the Pew Research accounts, that
we actually use him in our unit tests. (This - and *not* the fact that
he’s the greatest musician of all time - is the reason that he’s in our
example!)

.. code:: ipython3

    profiles = TwitterProfileSet.objects.get(name="my_profile_set").profiles.all()

.. code:: ipython3

    from django_twitter.utils import identify_unusual_profiles_by_tweet_text
    most_similar, most_unique = identify_unusual_profiles_by_tweet_text(profiles)
    most_unique


.. parsed-literal::

    Gathering tweet text: 100%|██████████| 11/11 [00:00<00:00, 90.31it/s]




.. raw:: html

    <div>
    <style scoped>
        .dataframe tbody tr th:only-of-type {
            vertical-align: middle;
        }
    
        .dataframe tbody tr th {
            vertical-align: top;
        }
    
        .dataframe thead th {
            text-align: right;
        }
    </style>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th></th>
          <th>twitter_id</th>
          <th>tweet_text</th>
          <th>avg_cosine</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>0</th>
          <td>27260086</td>
          <td>RT @MIAFestival: LINEUP ALERT!\nJustin Bieber,...</td>
          <td>0.504817</td>
        </tr>
      </tbody>
    </table>
    </div>



.. code:: ipython3

    from django_twitter.utils import identify_unusual_profiles_by_descriptions
    most_similar, most_unique = identify_unusual_profiles_by_descriptions(profiles)
    most_unique




.. raw:: html

    <div>
    <style scoped>
        .dataframe tbody tr th:only-of-type {
            vertical-align: middle;
        }
    
        .dataframe tbody tr th {
            vertical-align: top;
        }
    
        .dataframe thead th {
            text-align: right;
        }
    </style>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th></th>
          <th>twitter_id</th>
          <th>snapshots__description</th>
          <th>avg_cosine</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>5</th>
          <td>27260086</td>
          <td>JUSTICE the album out now</td>
          <td>0.163522</td>
        </tr>
      </tbody>
    </table>
    </div>



Even if you have a perfect account roster with no accidental Biebers,
different Twitter accounts posts at different rates, and Twitter only
provides each account’s ~3200 most recent tweets. If you’re interested
in doing any sort of historical analysis on any period prior to when you
began regular data collection, you’re going to need to assess how far
back the backfill process got you. You may have years’ worth of tweets
for some accounts, but only weeks for others.

Django Twitter provides two functions to assess tweet coverage over time
for a set of profiles you’re interested in. The
``get_monthly_twitter_activity`` function produces a spreadsheet where
every row is an account and every column is a month, across whatever
timeframe you request. The cells contain how many tweets exist in the
database for each profile/month, and if you load this spreadsheet into
Excel and do some conditional formatting to highlight empty cells, it
makes it super easy to tell how far back you can reasonably analyze data
without losing a ton of coverage.

.. code:: ipython3

    import datetime
    from django_twitter.utils import get_monthly_twitter_activity
    results = get_monthly_twitter_activity(
        profiles,
        datetime.date(2018, 1, 1),
        max_date=datetime.datetime.now().date() + datetime.timedelta(days=1),
    )

.. code:: ipython3

    results




.. raw:: html

    <div>
    <style scoped>
        .dataframe tbody tr th:only-of-type {
            vertical-align: middle;
        }
    
        .dataframe tbody tr th {
            vertical-align: top;
        }
    
        .dataframe thead th {
            text-align: right;
        }
    </style>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th></th>
          <th>2020_12</th>
          <th>2021_1</th>
          <th>2021_2</th>
          <th>2021_3</th>
          <th>2021_4</th>
          <th>2021_5</th>
          <th>2021_6</th>
          <th>pk</th>
          <th>screen_name</th>
          <th>created_at</th>
          <th>name</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>1.0</th>
          <td>0.0</td>
          <td>1.0</td>
          <td>0.0</td>
          <td>0.0</td>
          <td>1.0</td>
          <td>3.0</td>
          <td>29.0</td>
          <td>1.0</td>
          <td>pewresearch</td>
          <td>2009-03-03 10:39:39</td>
          <td>Pew Research Center</td>
        </tr>
        <tr>
          <th>4.0</th>
          <td>0.0</td>
          <td>0.0</td>
          <td>0.0</td>
          <td>0.0</td>
          <td>0.0</td>
          <td>0.0</td>
          <td>26.0</td>
          <td>2.0</td>
          <td>pewglobal</td>
          <td>2012-09-18 12:08:41</td>
          <td>Pew Research Global</td>
        </tr>
        <tr>
          <th>6.0</th>
          <td>0.0</td>
          <td>0.0</td>
          <td>0.0</td>
          <td>0.0</td>
          <td>0.0</td>
          <td>0.0</td>
          <td>25.0</td>
          <td>3.0</td>
          <td>pewmethods</td>
          <td>2015-02-09 16:00:41</td>
          <td>Pew Research Methods</td>
        </tr>
        <tr>
          <th>8.0</th>
          <td>0.0</td>
          <td>0.0</td>
          <td>0.0</td>
          <td>0.0</td>
          <td>0.0</td>
          <td>0.0</td>
          <td>25.0</td>
          <td>4.0</td>
          <td>pewjournalism</td>
          <td>2010-02-04 09:42:57</td>
          <td>Pew Research Journalism</td>
        </tr>
        <tr>
          <th>3.0</th>
          <td>0.0</td>
          <td>0.0</td>
          <td>0.0</td>
          <td>0.0</td>
          <td>2.0</td>
          <td>27.0</td>
          <td>2.0</td>
          <td>5.0</td>
          <td>facttank</td>
          <td>2013-03-13 18:41:33</td>
          <td>Pew Research Fact Tank</td>
        </tr>
        <tr>
          <th>7.0</th>
          <td>0.0</td>
          <td>0.0</td>
          <td>0.0</td>
          <td>0.0</td>
          <td>0.0</td>
          <td>0.0</td>
          <td>25.0</td>
          <td>6.0</td>
          <td>pewscience</td>
          <td>2013-03-12 14:42:00</td>
          <td>Pew Research Science</td>
        </tr>
        <tr>
          <th>9.0</th>
          <td>0.0</td>
          <td>0.0</td>
          <td>0.0</td>
          <td>0.0</td>
          <td>0.0</td>
          <td>8.0</td>
          <td>17.0</td>
          <td>7.0</td>
          <td>pewreligion</td>
          <td>2009-04-29 15:03:06</td>
          <td>Pew Research Religion</td>
        </tr>
        <tr>
          <th>2.0</th>
          <td>0.0</td>
          <td>0.0</td>
          <td>0.0</td>
          <td>0.0</td>
          <td>6.0</td>
          <td>14.0</td>
          <td>5.0</td>
          <td>8.0</td>
          <td>pewhispanic</td>
          <td>2011-12-01 13:26:52</td>
          <td>PewResearch Hispanic</td>
        </tr>
        <tr>
          <th>5.0</th>
          <td>0.0</td>
          <td>0.0</td>
          <td>0.0</td>
          <td>0.0</td>
          <td>0.0</td>
          <td>0.0</td>
          <td>25.0</td>
          <td>9.0</td>
          <td>pewinternet</td>
          <td>2008-10-30 13:40:17</td>
          <td>Pew Research Internet</td>
        </tr>
        <tr>
          <th>10.0</th>
          <td>1.0</td>
          <td>15.0</td>
          <td>0.0</td>
          <td>8.0</td>
          <td>1.0</td>
          <td>0.0</td>
          <td>0.0</td>
          <td>10.0</td>
          <td>pvankessel</td>
          <td>2012-03-19 22:58:08</td>
          <td>Patrick van Kessel</td>
        </tr>
        <tr>
          <th>0.0</th>
          <td>0.0</td>
          <td>0.0</td>
          <td>0.0</td>
          <td>0.0</td>
          <td>7.0</td>
          <td>7.0</td>
          <td>11.0</td>
          <td>11.0</td>
          <td>justinbieber</td>
          <td>2009-03-28 11:41:22</td>
          <td>Justin Bieber</td>
        </tr>
      </tbody>
    </table>
    </div>



The second function, ``find_missing_date_ranges``, scans a time period
and returns a dataframe of all periods of at least N consecutive days
where a profile doesn’t have any tweets in the database. This can be
useful to search around for weird anomalies that may have been caused by
data collection errors, or temporarily suspended accounts, etc.

.. code:: ipython3

    from django_twitter.utils import find_missing_date_ranges
    results = find_missing_date_ranges(
        profiles,
        datetime.date(2021, 1, 1),
        max_date=datetime.datetime.now().date() + datetime.timedelta(days=1),
        min_consecutive_missing_dates=5,
    )


.. parsed-literal::

    Scanning profiles for missing dates: 100%|██████████| 11/11 [00:00<00:00, 189.21it/s]


.. code:: ipython3

    results




.. raw:: html

    <div>
    <style scoped>
        .dataframe tbody tr th:only-of-type {
            vertical-align: middle;
        }
    
        .dataframe tbody tr th {
            vertical-align: top;
        }
    
        .dataframe thead th {
            text-align: right;
        }
    </style>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th></th>
          <th>twitter_id</th>
          <th>start_date</th>
          <th>end_date</th>
          <th>range</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>23</th>
          <td>111339670</td>
          <td>2021-01-01</td>
          <td>2021-06-11</td>
          <td>161</td>
        </tr>
        <tr>
          <th>22</th>
          <td>1262729180</td>
          <td>2021-01-01</td>
          <td>2021-06-03</td>
          <td>153</td>
        </tr>
        <tr>
          <th>21</th>
          <td>3015897974</td>
          <td>2021-01-01</td>
          <td>2021-06-02</td>
          <td>152</td>
        </tr>
        <tr>
          <th>20</th>
          <td>17071048</td>
          <td>2021-01-01</td>
          <td>2021-06-01</td>
          <td>151</td>
        </tr>
        <tr>
          <th>18</th>
          <td>831470472</td>
          <td>2021-01-01</td>
          <td>2021-06-01</td>
          <td>151</td>
        </tr>
        <tr>
          <th>24</th>
          <td>36462231</td>
          <td>2021-01-01</td>
          <td>2021-05-25</td>
          <td>144</td>
        </tr>
        <tr>
          <th>14</th>
          <td>1265726480</td>
          <td>2021-01-01</td>
          <td>2021-04-27</td>
          <td>116</td>
        </tr>
        <tr>
          <th>10</th>
          <td>426041590</td>
          <td>2021-01-01</td>
          <td>2021-04-22</td>
          <td>111</td>
        </tr>
        <tr>
          <th>6</th>
          <td>22642788</td>
          <td>2021-01-16</td>
          <td>2021-04-30</td>
          <td>104</td>
        </tr>
        <tr>
          <th>0</th>
          <td>27260086</td>
          <td>2021-01-01</td>
          <td>2021-04-13</td>
          <td>102</td>
        </tr>
        <tr>
          <th>29</th>
          <td>530977797</td>
          <td>2021-04-27</td>
          <td>2021-06-16</td>
          <td>50</td>
        </tr>
        <tr>
          <th>28</th>
          <td>530977797</td>
          <td>2021-03-15</td>
          <td>2021-04-26</td>
          <td>42</td>
        </tr>
        <tr>
          <th>26</th>
          <td>530977797</td>
          <td>2021-01-26</td>
          <td>2021-03-05</td>
          <td>38</td>
        </tr>
        <tr>
          <th>7</th>
          <td>22642788</td>
          <td>2021-05-05</td>
          <td>2021-05-22</td>
          <td>17</td>
        </tr>
        <tr>
          <th>5</th>
          <td>22642788</td>
          <td>2021-01-01</td>
          <td>2021-01-15</td>
          <td>14</td>
        </tr>
        <tr>
          <th>25</th>
          <td>530977797</td>
          <td>2021-01-01</td>
          <td>2021-01-15</td>
          <td>14</td>
        </tr>
        <tr>
          <th>15</th>
          <td>1265726480</td>
          <td>2021-05-06</td>
          <td>2021-05-20</td>
          <td>14</td>
        </tr>
        <tr>
          <th>4</th>
          <td>27260086</td>
          <td>2021-05-25</td>
          <td>2021-06-06</td>
          <td>12</td>
        </tr>
        <tr>
          <th>19</th>
          <td>831470472</td>
          <td>2021-06-02</td>
          <td>2021-06-11</td>
          <td>9</td>
        </tr>
        <tr>
          <th>3</th>
          <td>27260086</td>
          <td>2021-05-15</td>
          <td>2021-05-24</td>
          <td>9</td>
        </tr>
        <tr>
          <th>17</th>
          <td>1265726480</td>
          <td>2021-06-08</td>
          <td>2021-06-16</td>
          <td>8</td>
        </tr>
        <tr>
          <th>12</th>
          <td>426041590</td>
          <td>2021-05-26</td>
          <td>2021-06-03</td>
          <td>8</td>
        </tr>
        <tr>
          <th>8</th>
          <td>22642788</td>
          <td>2021-05-26</td>
          <td>2021-06-02</td>
          <td>7</td>
        </tr>
        <tr>
          <th>1</th>
          <td>27260086</td>
          <td>2021-04-14</td>
          <td>2021-04-20</td>
          <td>6</td>
        </tr>
        <tr>
          <th>9</th>
          <td>22642788</td>
          <td>2021-06-08</td>
          <td>2021-06-14</td>
          <td>6</td>
        </tr>
        <tr>
          <th>11</th>
          <td>426041590</td>
          <td>2021-05-06</td>
          <td>2021-05-12</td>
          <td>6</td>
        </tr>
        <tr>
          <th>16</th>
          <td>1265726480</td>
          <td>2021-06-02</td>
          <td>2021-06-07</td>
          <td>5</td>
        </tr>
        <tr>
          <th>2</th>
          <td>27260086</td>
          <td>2021-04-28</td>
          <td>2021-05-03</td>
          <td>5</td>
        </tr>
        <tr>
          <th>27</th>
          <td>530977797</td>
          <td>2021-03-09</td>
          <td>2021-03-14</td>
          <td>5</td>
        </tr>
        <tr>
          <th>13</th>
          <td>426041590</td>
          <td>2021-06-09</td>
          <td>2021-06-14</td>
          <td>5</td>
        </tr>
      </tbody>
    </table>
    </div>



Extracting/exporting data
-------------------------

Finally, let’s take a look at exporting our data. Often we want a giant
spreadsheet of tweets, or a spreadsheet of a profile’s data (like
follower counts) over time. The ``get_twitter_profile_dataframe`` can
grab the latter for you, and the ``get_tweet_dataframe`` function gives
you the former. Presumably we’ve inspected our tweet coverage using the
functions above and have determined that we don’t have any tweet
coverage issues, but when it comes to profile data, it’s possible that
we haven’t been collecting that as regularly, or we may have some gaps
in our timeseries. To help with this, the
``get_twitter_profile_dataframe`` function uses linear interpolation
(for numerical values) and front-filling (for fixed attributes like
descriptions) to fill in gaps where it can and provide you with a
complete day-by-day profile dataframe that can be merged in with tweets
on the days they were created.

Since we just started collecting data, we only have profile snapshots
for today. So to illustrate how the interpolation works, we’re going to
create a fake snapshot on that historic and fateful day when Justin
Bieber first joined Twitter in 2009, and we’re just going to approximate
his followers by assuming that they’ve increased at a steady linear
rate. (This is obviously a poor assumption, but it works really well for
shorter periods, which is all you should have to fill in if you’ve been
collecting data at least somewhat regularly and aren’t making fake
decade-old datapoints like I am.)

.. code:: ipython3

    from testapp.models import TwitterProfileSnapshot
    justin = TwitterProfile.objects.get(twitter_id="27260086")
    fake_snapshot = TwitterProfileSnapshot.objects.create(
        profile=justin,
        screen_name=justin.most_recent_snapshot.screen_name,
        followers_count=0,
        favorites_count=0,
        followings_count=0,
        statuses_count=0
    )
    fake_snapshot.timestamp = justin.created_at
    fake_snapshot.save()

Now let’s get our dataframe

.. code:: ipython3

    from django_twitter.utils import get_twitter_profile_dataframe
    df = get_twitter_profile_dataframe(
        profiles, datetime.datetime(2021, 1, 1), datetime.datetime.now(), skip_interpolation=False
    )
    df[df['twitter_id']=="27260086"].dropna(subset=['followers_count'])


.. parsed-literal::

    Extracting Twitter profile snapshots: 100%|██████████| 11/11 [00:00<00:00, 13.85it/s]




.. raw:: html

    <div>
    <style scoped>
        .dataframe tbody tr th:only-of-type {
            vertical-align: middle;
        }
    
        .dataframe tbody tr th {
            vertical-align: top;
        }
    
        .dataframe thead th {
            text-align: right;
        }
    </style>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th></th>
          <th>date</th>
          <th>description</th>
          <th>followers_count</th>
          <th>favorites_count</th>
          <th>followings_count</th>
          <th>listed_count</th>
          <th>statuses_count</th>
          <th>name</th>
          <th>screen_name</th>
          <th>status</th>
          <th>is_verified</th>
          <th>is_protected</th>
          <th>location</th>
          <th>created_at</th>
          <th>twitter_error_code</th>
          <th>twitter_id</th>
          <th>pk</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>4297</th>
          <td>2021-01-01</td>
          <td></td>
          <td>1.096499e+08</td>
          <td>4416.414612</td>
          <td>278319.829449</td>
          <td>NaN</td>
          <td>30215.748991</td>
          <td></td>
          <td>justinbieber</td>
          <td></td>
          <td>None</td>
          <td>None</td>
          <td></td>
          <td>2009-03-28 11:41:22</td>
          <td>None</td>
          <td>27260086</td>
          <td>11</td>
        </tr>
        <tr>
          <th>4298</th>
          <td>2021-01-02</td>
          <td></td>
          <td>1.096755e+08</td>
          <td>4417.442403</td>
          <td>278384.600179</td>
          <td>NaN</td>
          <td>30222.780816</td>
          <td></td>
          <td>justinbieber</td>
          <td></td>
          <td>None</td>
          <td>None</td>
          <td></td>
          <td>2009-03-28 11:41:22</td>
          <td>None</td>
          <td>27260086</td>
          <td>11</td>
        </tr>
        <tr>
          <th>4299</th>
          <td>2021-01-03</td>
          <td></td>
          <td>1.097010e+08</td>
          <td>4418.470193</td>
          <td>278449.370910</td>
          <td>NaN</td>
          <td>30229.812640</td>
          <td></td>
          <td>justinbieber</td>
          <td></td>
          <td>None</td>
          <td>None</td>
          <td></td>
          <td>2009-03-28 11:41:22</td>
          <td>None</td>
          <td>27260086</td>
          <td>11</td>
        </tr>
        <tr>
          <th>4300</th>
          <td>2021-01-04</td>
          <td></td>
          <td>1.097265e+08</td>
          <td>4419.497983</td>
          <td>278514.141641</td>
          <td>NaN</td>
          <td>30236.844464</td>
          <td></td>
          <td>justinbieber</td>
          <td></td>
          <td>None</td>
          <td>None</td>
          <td></td>
          <td>2009-03-28 11:41:22</td>
          <td>None</td>
          <td>27260086</td>
          <td>11</td>
        </tr>
        <tr>
          <th>4301</th>
          <td>2021-01-05</td>
          <td></td>
          <td>1.097520e+08</td>
          <td>4420.525773</td>
          <td>278578.912371</td>
          <td>NaN</td>
          <td>30243.876289</td>
          <td></td>
          <td>justinbieber</td>
          <td></td>
          <td>None</td>
          <td>None</td>
          <td></td>
          <td>2009-03-28 11:41:22</td>
          <td>None</td>
          <td>27260086</td>
          <td>11</td>
        </tr>
        <tr>
          <th>...</th>
          <td>...</td>
          <td>...</td>
          <td>...</td>
          <td>...</td>
          <td>...</td>
          <td>...</td>
          <td>...</td>
          <td>...</td>
          <td>...</td>
          <td>...</td>
          <td>...</td>
          <td>...</td>
          <td>...</td>
          <td>...</td>
          <td>...</td>
          <td>...</td>
          <td>...</td>
        </tr>
        <tr>
          <th>4458</th>
          <td>2021-06-11</td>
          <td></td>
          <td>1.137583e+08</td>
          <td>4581.888839</td>
          <td>288747.917078</td>
          <td>NaN</td>
          <td>31347.872703</td>
          <td></td>
          <td>justinbieber</td>
          <td></td>
          <td>None</td>
          <td>None</td>
          <td></td>
          <td>2009-03-28 11:41:22</td>
          <td>None</td>
          <td>27260086</td>
          <td>11</td>
        </tr>
        <tr>
          <th>4459</th>
          <td>2021-06-12</td>
          <td></td>
          <td>1.137838e+08</td>
          <td>4582.916629</td>
          <td>288812.687808</td>
          <td>NaN</td>
          <td>31354.904527</td>
          <td></td>
          <td>justinbieber</td>
          <td></td>
          <td>None</td>
          <td>None</td>
          <td></td>
          <td>2009-03-28 11:41:22</td>
          <td>None</td>
          <td>27260086</td>
          <td>11</td>
        </tr>
        <tr>
          <th>4460</th>
          <td>2021-06-13</td>
          <td></td>
          <td>1.138093e+08</td>
          <td>4583.944420</td>
          <td>288877.458539</td>
          <td>NaN</td>
          <td>31361.936351</td>
          <td></td>
          <td>justinbieber</td>
          <td></td>
          <td>None</td>
          <td>None</td>
          <td></td>
          <td>2009-03-28 11:41:22</td>
          <td>None</td>
          <td>27260086</td>
          <td>11</td>
        </tr>
        <tr>
          <th>4461</th>
          <td>2021-06-14</td>
          <td></td>
          <td>1.138349e+08</td>
          <td>4584.972210</td>
          <td>288942.229269</td>
          <td>NaN</td>
          <td>31368.968176</td>
          <td></td>
          <td>justinbieber</td>
          <td></td>
          <td>None</td>
          <td>None</td>
          <td></td>
          <td>2009-03-28 11:41:22</td>
          <td>None</td>
          <td>27260086</td>
          <td>11</td>
        </tr>
        <tr>
          <th>4462</th>
          <td>2021-06-15</td>
          <td>JUSTICE the album out now</td>
          <td>1.138604e+08</td>
          <td>4586.000000</td>
          <td>289007.000000</td>
          <td>543037.0</td>
          <td>31376.000000</td>
          <td>Justin Bieber</td>
          <td>justinbieber</td>
          <td>RT @MIAFestival: LINEUP ALERT!\nJustin Bieber,...</td>
          <td>True</td>
          <td>False</td>
          <td>The 6</td>
          <td>2009-03-28 11:41:22</td>
          <td>None</td>
          <td>27260086</td>
          <td>11</td>
        </tr>
      </tbody>
    </table>
    <p>166 rows × 17 columns</p>
    </div>



If we want tweets, it’s a very similar process

.. code:: ipython3

    from django_twitter.utils import get_tweet_dataframe
    get_tweet_dataframe(
        profiles, datetime.datetime(2021, 1, 1), datetime.datetime.now()
    )




.. raw:: html

    <div>
    <style scoped>
        .dataframe tbody tr th:only-of-type {
            vertical-align: middle;
        }
    
        .dataframe tbody tr th {
            vertical-align: top;
        }
    
        .dataframe thead th {
            text-align: right;
        }
    </style>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th></th>
          <th>pk</th>
          <th>twitter_id</th>
          <th>last_update_time</th>
          <th>historical</th>
          <th>created_at</th>
          <th>text</th>
          <th>retweet_count</th>
          <th>favorite_count</th>
          <th>profile</th>
          <th>retweeted_status</th>
          <th>in_reply_to_status</th>
          <th>quoted_status</th>
          <th>date</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>0</th>
          <td>1</td>
          <td>1404865073684828161</td>
          <td>2021-06-15 14:28:19.218205-04:00</td>
          <td>False</td>
          <td>2021-06-15 13:15:09-04:00</td>
          <td>@Katrina_HRM You might also enjoy our short em...</td>
          <td>1</td>
          <td>2</td>
          <td>22642788</td>
          <td>None</td>
          <td>1404850695715659777</td>
          <td>None</td>
          <td>2021-06-15</td>
        </tr>
        <tr>
          <th>1</th>
          <td>30</td>
          <td>1404502650398330885</td>
          <td>2021-06-15 14:28:20.497058-04:00</td>
          <td>False</td>
          <td>2021-06-14 13:15:00-04:00</td>
          <td>These are just a few of our findings from our ...</td>
          <td>3</td>
          <td>5</td>
          <td>22642788</td>
          <td>None</td>
          <td>1404502648309620743</td>
          <td>None</td>
          <td>2021-06-14</td>
        </tr>
        <tr>
          <th>2</th>
          <td>31</td>
          <td>1404502648309620743</td>
          <td>2021-06-15 14:28:20.541835-04:00</td>
          <td>False</td>
          <td>2021-06-14 13:15:00-04:00</td>
          <td>Many of these posts linked to their own conten...</td>
          <td>1</td>
          <td>2</td>
          <td>22642788</td>
          <td>None</td>
          <td>1404502645281263616</td>
          <td>None</td>
          <td>2021-06-14</td>
        </tr>
        <tr>
          <th>3</th>
          <td>32</td>
          <td>1404502645281263616</td>
          <td>2021-06-15 14:28:20.583141-04:00</td>
          <td>False</td>
          <td>2021-06-14 13:14:59-04:00</td>
          <td>59% of posts studied linked to a site outside ...</td>
          <td>0</td>
          <td>1</td>
          <td>22642788</td>
          <td>None</td>
          <td>1404502642919972869</td>
          <td>None</td>
          <td>2021-06-14</td>
        </tr>
        <tr>
          <th>4</th>
          <td>34</td>
          <td>1404502638482317312</td>
          <td>2021-06-15 14:28:20.699133-04:00</td>
          <td>False</td>
          <td>2021-06-14 13:14:58-04:00</td>
          <td>Beyond a post's main topic, researchers also a...</td>
          <td>1</td>
          <td>1</td>
          <td>22642788</td>
          <td>None</td>
          <td>1404502634728411136</td>
          <td>None</td>
          <td>2021-06-14</td>
        </tr>
        <tr>
          <th>...</th>
          <td>...</td>
          <td>...</td>
          <td>...</td>
          <td>...</td>
          <td>...</td>
          <td>...</td>
          <td>...</td>
          <td>...</td>
          <td>...</td>
          <td>...</td>
          <td>...</td>
          <td>...</td>
          <td>...</td>
        </tr>
        <tr>
          <th>285</th>
          <td>23</td>
          <td>1404534507055816705</td>
          <td>2021-06-15 14:28:20.230611-04:00</td>
          <td>False</td>
          <td>2021-06-14 15:21:36-04:00</td>
          <td>RT @GalenStocking: 🚨 NEW REPORT 🚨: A study of ...</td>
          <td>5</td>
          <td>0</td>
          <td>22642788</td>
          <td>1404533972193906693</td>
          <td>None</td>
          <td>None</td>
          <td>2021-06-14</td>
        </tr>
        <tr>
          <th>286</th>
          <td>11</td>
          <td>1404836235521277955</td>
          <td>2021-06-15 14:28:19.654620-04:00</td>
          <td>False</td>
          <td>2021-06-15 11:20:33-04:00</td>
          <td>RT @pewmethods: To study how 25 popular curren...</td>
          <td>1</td>
          <td>0</td>
          <td>22642788</td>
          <td>1404829803329593344</td>
          <td>None</td>
          <td>None</td>
          <td>2021-06-15</td>
        </tr>
        <tr>
          <th>287</th>
          <td>9</td>
          <td>1404836281985740801</td>
          <td>2021-06-15 14:28:19.558623-04:00</td>
          <td>False</td>
          <td>2021-06-15 11:20:44-04:00</td>
          <td>RT @pewinternet: Join us and @DataDotOrg tomor...</td>
          <td>2</td>
          <td>0</td>
          <td>22642788</td>
          <td>1404831838397505540</td>
          <td>None</td>
          <td>None</td>
          <td>2021-06-15</td>
        </tr>
        <tr>
          <th>288</th>
          <td>91</td>
          <td>1404851306511089676</td>
          <td>2021-06-15 14:27:59.802896-04:00</td>
          <td>False</td>
          <td>2021-06-15 12:20:27-04:00</td>
          <td>RT @_StephKramer: 1) Quick thread with some fi...</td>
          <td>5</td>
          <td>0</td>
          <td>36462231</td>
          <td>1404846387750215682</td>
          <td>None</td>
          <td>None</td>
          <td>2021-06-15</td>
        </tr>
        <tr>
          <th>289</th>
          <td>5</td>
          <td>1404847185922035721</td>
          <td>2021-06-15 14:28:19.385485-04:00</td>
          <td>False</td>
          <td>2021-06-15 12:04:04-04:00</td>
          <td>RT @_StephKramer: 1) Quick thread with some fi...</td>
          <td>5</td>
          <td>0</td>
          <td>22642788</td>
          <td>1404846387750215682</td>
          <td>None</td>
          <td>None</td>
          <td>2021-06-15</td>
        </tr>
      </tbody>
    </table>
    <p>290 rows × 13 columns</p>
    </div>



.. code:: ipython3

    from django_twitter.utils import get_tweet_dataframe
    profiles = TwitterProfileSet.objects.get(name="my_profile_set").profiles.all()
    get_tweet_dataframe(
        profiles, datetime.datetime(2021, 1, 1), datetime.datetime.now()
    )




.. raw:: html

    <div>
    <style scoped>
        .dataframe tbody tr th:only-of-type {
            vertical-align: middle;
        }
    
        .dataframe tbody tr th {
            vertical-align: top;
        }
    
        .dataframe thead th {
            text-align: right;
        }
    </style>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th></th>
          <th>pk</th>
          <th>twitter_id</th>
          <th>last_update_time</th>
          <th>historical</th>
          <th>created_at</th>
          <th>text</th>
          <th>retweet_count</th>
          <th>favorite_count</th>
          <th>profile</th>
          <th>retweeted_status</th>
          <th>in_reply_to_status</th>
          <th>quoted_status</th>
          <th>date</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>0</th>
          <td>1</td>
          <td>1404865073684828161</td>
          <td>2021-06-15 14:28:19.218205-04:00</td>
          <td>False</td>
          <td>2021-06-15 13:15:09-04:00</td>
          <td>@Katrina_HRM You might also enjoy our short em...</td>
          <td>1</td>
          <td>2</td>
          <td>22642788</td>
          <td>None</td>
          <td>1404850695715659777</td>
          <td>None</td>
          <td>2021-06-15</td>
        </tr>
        <tr>
          <th>1</th>
          <td>30</td>
          <td>1404502650398330885</td>
          <td>2021-06-15 14:28:20.497058-04:00</td>
          <td>False</td>
          <td>2021-06-14 13:15:00-04:00</td>
          <td>These are just a few of our findings from our ...</td>
          <td>3</td>
          <td>5</td>
          <td>22642788</td>
          <td>None</td>
          <td>1404502648309620743</td>
          <td>None</td>
          <td>2021-06-14</td>
        </tr>
        <tr>
          <th>2</th>
          <td>31</td>
          <td>1404502648309620743</td>
          <td>2021-06-15 14:28:20.541835-04:00</td>
          <td>False</td>
          <td>2021-06-14 13:15:00-04:00</td>
          <td>Many of these posts linked to their own conten...</td>
          <td>1</td>
          <td>2</td>
          <td>22642788</td>
          <td>None</td>
          <td>1404502645281263616</td>
          <td>None</td>
          <td>2021-06-14</td>
        </tr>
        <tr>
          <th>3</th>
          <td>32</td>
          <td>1404502645281263616</td>
          <td>2021-06-15 14:28:20.583141-04:00</td>
          <td>False</td>
          <td>2021-06-14 13:14:59-04:00</td>
          <td>59% of posts studied linked to a site outside ...</td>
          <td>0</td>
          <td>1</td>
          <td>22642788</td>
          <td>None</td>
          <td>1404502642919972869</td>
          <td>None</td>
          <td>2021-06-14</td>
        </tr>
        <tr>
          <th>4</th>
          <td>34</td>
          <td>1404502638482317312</td>
          <td>2021-06-15 14:28:20.699133-04:00</td>
          <td>False</td>
          <td>2021-06-14 13:14:58-04:00</td>
          <td>Beyond a post's main topic, researchers also a...</td>
          <td>1</td>
          <td>1</td>
          <td>22642788</td>
          <td>None</td>
          <td>1404502634728411136</td>
          <td>None</td>
          <td>2021-06-14</td>
        </tr>
        <tr>
          <th>...</th>
          <td>...</td>
          <td>...</td>
          <td>...</td>
          <td>...</td>
          <td>...</td>
          <td>...</td>
          <td>...</td>
          <td>...</td>
          <td>...</td>
          <td>...</td>
          <td>...</td>
          <td>...</td>
          <td>...</td>
        </tr>
        <tr>
          <th>285</th>
          <td>23</td>
          <td>1404534507055816705</td>
          <td>2021-06-15 14:28:20.230611-04:00</td>
          <td>False</td>
          <td>2021-06-14 15:21:36-04:00</td>
          <td>RT @GalenStocking: 🚨 NEW REPORT 🚨: A study of ...</td>
          <td>5</td>
          <td>0</td>
          <td>22642788</td>
          <td>1404533972193906693</td>
          <td>None</td>
          <td>None</td>
          <td>2021-06-14</td>
        </tr>
        <tr>
          <th>286</th>
          <td>11</td>
          <td>1404836235521277955</td>
          <td>2021-06-15 14:28:19.654620-04:00</td>
          <td>False</td>
          <td>2021-06-15 11:20:33-04:00</td>
          <td>RT @pewmethods: To study how 25 popular curren...</td>
          <td>1</td>
          <td>0</td>
          <td>22642788</td>
          <td>1404829803329593344</td>
          <td>None</td>
          <td>None</td>
          <td>2021-06-15</td>
        </tr>
        <tr>
          <th>287</th>
          <td>9</td>
          <td>1404836281985740801</td>
          <td>2021-06-15 14:28:19.558623-04:00</td>
          <td>False</td>
          <td>2021-06-15 11:20:44-04:00</td>
          <td>RT @pewinternet: Join us and @DataDotOrg tomor...</td>
          <td>2</td>
          <td>0</td>
          <td>22642788</td>
          <td>1404831838397505540</td>
          <td>None</td>
          <td>None</td>
          <td>2021-06-15</td>
        </tr>
        <tr>
          <th>288</th>
          <td>91</td>
          <td>1404851306511089676</td>
          <td>2021-06-15 14:27:59.802896-04:00</td>
          <td>False</td>
          <td>2021-06-15 12:20:27-04:00</td>
          <td>RT @_StephKramer: 1) Quick thread with some fi...</td>
          <td>5</td>
          <td>0</td>
          <td>36462231</td>
          <td>1404846387750215682</td>
          <td>None</td>
          <td>None</td>
          <td>2021-06-15</td>
        </tr>
        <tr>
          <th>289</th>
          <td>5</td>
          <td>1404847185922035721</td>
          <td>2021-06-15 14:28:19.385485-04:00</td>
          <td>False</td>
          <td>2021-06-15 12:04:04-04:00</td>
          <td>RT @_StephKramer: 1) Quick thread with some fi...</td>
          <td>5</td>
          <td>0</td>
          <td>22642788</td>
          <td>1404846387750215682</td>
          <td>None</td>
          <td>None</td>
          <td>2021-06-15</td>
        </tr>
      </tbody>
    </table>
    <p>290 rows × 13 columns</p>
    </div>


