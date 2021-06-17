*************************************
Getting Started
*************************************

Configuration
~~~~~~~~~~~~~

Django Twitter is not designed to be a standalone app - rather, it is
designed to provide abstract models for you to import and implement in
your own Django app. This gives you more flexibility when it comes to
creating relations between the Twitter data you collect and other models
in your app, and allows you to expand the models with additional custom
fields as needed. For example, one our projects consists of an extensive
database of members of Congress and other politicians, including their
Twitter profiles. Using Django Twitter abstract models, we can define a
standard template for storing Twitter profile data, but also expand it
with a foreign key to associate profiles with particular politicians in
our database, like so:

.. code:: python

    from django_twitter.models import AbstractTwitterProfile

    class TwitterProfile(AbstractTwitterProfile):
        politician = models.ForeignKey("Politician", related_name="twitter_profiles")

To implement Django Twitter models in your app, you simply need to
import the abstract models you wish to create in your own app's
``models.py`` file. If you don't want to make any modifications to the
models, you can simply implement them as defined, like so:

.. code:: python

    from django_twitter.models import *

    class TwitterProfile(AbstractTwitterProfile):
        pass

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

    **NOTE FOR DEVELOPERS:** Because Django Twitter models are abstract
    and get implemented within your own app, Django Twitter doesn't have
    any clue where its models actually live and what they're called.
    Because of this, Django Twitter creates relations between your app's
    implementations of its models in a somewhat unconventional way: all
    of the abstract models in Django Twitter inherit from an
    ``AbstractTwitterBase`` class that has a custom ``__new__`` function
    that adds relations to your concrete models at runtime, when they
    get initialized. Since this happens when Django itself first
    initializes, ``AbstractTwitterBase`` objects are able to
    self-recognize themselves and create their own relations, which
    Django recognizes as though they had been included in the model
    definitions directly. Unless you want to make changes directly to
    Django Twitter's abstract models as a developer, this should have no
    impact on how you use Django Twitter. But if you do wish to modify
    or expand relations between any of the abstract models defined in
    Django Twitter, you will need to do so by editing the ``__new__``
    function on ``AbstractTwitterBase``.

Then, in your ``settings.py`` file, you simply need to add
``django_twitter`` to your ``INSTALLED_APPS`` and define a single
additional settings variable that tells Django Twitter the name of the
app that implements the abstract models, like so:

.. code:: python

    TWITTER_APP = "my_app"

Once you've done this, you just need to run
``python manage.py makemigrations my_app`` and
``python manage.py migrate`` to create the tables in your database.
You're now ready to start collecting and storing Twitter data. To do so,
you just need to call one of Django Twitter's data collection commands.

Twitter API credentials
~~~~~~~~~~~~~~~~~~~~~~~

All of the data collection commands in Django Twitter accept your
Twitter API access tokens and secrets directly as parameters:
``--api_key``, ``--api_secret``, ``--access_token``,
``--access_secret``. However, the Pewhooks ``TwitterAPIHandler`` that
Django Twitter uses also looks for your API credentials in environment
variables, and this is the preferred way to manage your credentials. If
you define the following variables, Django Twitter and Pewhooks will
automatically detect your credentials: ``TWITTER_API_KEY``,
``TWITTER_API_SECRET``, ``TWITTER_API_ACCESS_TOKEN``,
``TWITTER_API_ACCESS_SECRET``.

Data collection commands
~~~~~~~~~~~~~~~~~~~~~~~~

Django Twitter provides a set of Django management commands to cover all
of your data collection needs; collecting data outside of these commands
is not officially supported and not recommended. You can call these
commands using the CLI, for example:
``python manage.py django_twitter_get_profile MY_TWITTER_ID_OR_SCREEN_NAME``.

Or you can call them programmatically using Django's ``call_command``
function:

.. code:: python

    from django.core.management import call_command
    call_command("django_twitter_get_profile", MY_TWITTER_ID_OR_SCREEN_NAME)

Profile sets
~~~~~~~~~~~~

In the example models above, you may have noticed a model called
``TwitterProfileSet`` that does not correspond to any data type that can
be collected from the Twitter API. This is a model that exists in Django
Twitter to make it easier to track lists of Twitter profiles. The model
is extremely simple - it consists entirely of an arbitrary ``name``
field and a many-to-many relation on the model in your app that inherits
from ``AbstractTwitterProfile``. All of the management commands that
Django Twitter provides that collect data on Twitter profiles have
implementations that can be run on a set of profiles all at once, to
make it easier to do bulk data collection. For example, the
``django_twitter_get_profile`` command collects profile data for a
specific Twitter account, and the ``django_twitter_get_profile_set``
does the exact same thing, except for a list of accounts that are
associated with a ``TwitterProfileSet`` in your database. Similarly, you
can run ``django_twitter_get_profile_tweets`` on a single Twitter
account, or you can run ``django_twitter_get_profile_set_tweets`` to
loop over and collect the timelines for an entire set of accounts (more
on this below).

Loading in a set screen names or Twitter IDs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

While Django Twitter has support for sampling tweets directly using the
Streaming API, most of our projects here at Pew typically focus on a
specific list of Twitter accounts, for which we collect profile and
tweet data on a regular basis.

If you have a set of screen names or Twitter IDs and you wish to collect
data for them using Django Twitter, there are two correct ways to do
this. The easiest approach is to use Django Twitter's built-in commands:

.. code:: python


    from django.core.management import call_command
    call_command("django_twitter_get_profile", MY_TWITTER_ID_OR_SCREEN_NAME)

As with all Django management commands, you can also call the command
directly from the CLI by running
``python manage.py django_twitter_get_profile MY_TWITTER_ID_OR_SCREEN_NAME``

Running the ``django_twitter_get_profile`` command allows you to pass
either a Twitter ID or screen name, and it will correctly handshake with
the API and create the record properly. You can then look up the record
like so:

.. code:: python

    # If you were using a Twitter ID:
    from myapp.models import MyTwitterProfileModel
    profile = MyTwitterProfileModel.objects.get(twitter_id=MY_TWITTER_ID)

    # If you were using a screen name:
    from myapp.models import MyTwitterProfileModel
    profile = MyTwitterProfileModel.objects.get(screen_name=MY_SCREEN_NAME.lower())

If you're working with a lot of IDs or screen names, it's probably
easier to create a TwitterProfileSet (described above) to track all of
the profiles you'll be creating. You can do this easily by passing a
unique name for your collection of profiles when running the
get\_profile command:

.. code:: python

    from django.core.management import call_command
    call_command("django_twitter_get_profile", MY_TWITTER_ID_OR_SCREEN_NAME, add_to_profile_set="my_profile_set")

    from myapp.models import MyTwitterProfileSetModel
    profiles = MyTwitterProfileSetModel.objects.get(name="my_profile_set").profiles.all()

The advantage to using a profile set is that it allows you to run
commands on all of the profiles at once, such as collecting the latest
data from the API:

.. code:: python

    call_command("django_twitter_get_profile_set", "my_profile_set")

The second alternative approach is to create the profiles manually using
the Django ORM. If you do this and you're using a list of screen names,
you need to first look up the unique Twitter ID from the API before
creating the record:

.. code:: python

    from pewhooks.twitter import TwitterAPIHandler
    from django_twitter.utils import get_twitter_profile_json, get_twitter_profile
    from myapp.models import MyTwitterProfileModel

    # Initialize a Pewhooks TwitterAPIHandler
    twitter = TwitterAPIHandler()
    # Grab the profile from the API, so you have it's actual Twitter ID
    twitter_json = get_twitter_profile_json(SCREEN_NAME, twitter)
    if twitter_json:
        # Create or fetch the profile
        # get_twitter_profile creates the profile if it doesn't already exist, but it ONLY WORKS ON TWITTER IDS
        profile = get_twitter_profile(twitter_json.id_str, create=True)
        # Alternatively you can just do this directy from the API, although get_twitter_profile is preferred
        profile, _ = MyTwitterProfileModel.objects.get_or_create(twitter_id=twitter_json.id_str)

If the second option above seems somewhat tedious, that's because it's
intended to be. *Twitter screen names are recyclable, so they are NOT an
effective way for tracking Twitter profiles.* If an account that you're
tracking gets deleted, someone else can create a new account with the
same username. If you're using the screen name to query the API, you
could very easily wind up collecting data for an entirely different
account without noticing it. Screen name recycling isn't often a major
concern for your average run-of-the-mill Twitter account, but it's
something that happens *very* frequently for prominent accounts like,
for example, prominent members of Congress that leave office and delete
their official PR accounts. Users can also change their screen names at
any time - also something that isn't very common among your typical
Twitter users, but something that *does* happen fairly frequently with
politicians who, for example, might change their handle from
``JudyForCongress`` to ``CongresswomanJudy`` when they get elected.

For these reasons, Django Twitter tracks accounts using their canonical,
unique Twitter IDs instead of screen names. It's perfectly fine to call
the ``django_twitter_get_profile`` command with a screen name when you
first load in an account (as long as you're sure that the screen name
isn't outdated), but we recommend immediately switching to the account's
canonical ``twitter_id`` as soon as you've collected profile data for
the first time. Better yet, you can use Django Twitter's
``TwitterProfileSet`` model to track a list of accounts once you've
loaded them in, and it will always use the ``twitter_id`` field to
collect data.

Checking accounts with Django Verifications
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you're loading in a list of accounts from an external data source,
you might not have any choice but to use screen names - unfortunately,
the practice of using Twitter IDs instead of screen names is not as
common as it should be, so sometimes screen names are all you have. If
that's the case, it's possible that some of the screen names in your
list have already been recycled before you even start your data
collection, so it's good practice to take a look at the profile data you
get back from the API after you first load in a set of accounts, to make
sure that each account is actually, for example, a politician, and not a
spam bot that snatched up a politician's old username.

To help with this endeavor, it can be useful to also install Django
Verifications, which provides a lightweight interface for verifying the
accuracy of important records in your database. We use Django
Verifications in concert with Django Twitter to manually review and
confirm Twitter profiles that we *think* belong to politicians. Every
time we start tracking an account and link it to a politician in our
database (using a foreign key that we added to our implementation of the
``AbstractTwitterProfile`` model), Django Verifications queues it up for
manual review. To do this, we simply have to install
``django_verifications`` by adding it to your ``INSTALLED_APPS`` in
``settings.py``, define a few extra fields in your Twitter profile
model's ``Meta`` attributes, and have your model inherit from
``django_verifications.models.VerifiedModel`` as well as
``django_twitter.models.AbstractTwitterProfile``, like so:

.. code:: python

        
    from django_twitter.models import AbstractTwitterProfile
    from django_verifications.models import VerifiedModel

    class TwitterProfile(AbstractTwitterProfile, VerifiedModel):
        politician = models.ForeignKey("Politician", related_name="twitter_profiles")
        class Meta(object):
            unique_together = ("twitter_id", "politician")
            fields_to_verify = ["politician"]
            verification_filters = [{"politician__isnull": False}]

Checking accounts with Django Twitter's built-in utilities
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Even if you don't want to go to the trouble of setting up Django
Verifications, it can still be a good idea to spot-check your data using
some of Django Twitter's utility functions. Often, when screen names are
recycled and claimed by a new account, the new account is distinctively
different than the prior owner (e.g. a politician's old handle getting
picked up by a spam bot that constantly tweets about bitcoin) - so we
can sometimes find bad accounts simply by looking for unusual content.
Given a QuerySet of profiles, Django Twitter has two functions that
calculate the average similarity of each profile against all others,
using either the profiles' descriptions, or a sample of recent tweets.
Here, Justin Bieber easily stands out in comparison to our Pew Research
Center accounts:

.. code:: python

    from django_twitter.utils import identify_unusual_profiles_by_descriptions
    most_similar, most_unique = identify_unusual_profiles_by_descriptions(profiles)
    >>> most_unique
      twitter_id     snapshots__description  avg_cosine
    5   27260086  JUSTICE the album out now    0.163522

    from django_twitter.utils import identify_unusual_profiles_by_tweet_text
    most_similar, most_unique = identify_unusual_profiles_by_tweet_text(profiles)
    >>> most_unique
       twitter_id                                         tweet_text  avg_cosine
    10   27260086  RT @MIAFestival: LINEUP ALERT!\nJustin Bieber,...    0.508597

Profile snapshots
~~~~~~~~~~~~~~~~~

Since profile attributes (e.g. screen names, descriptions) and profile
stats (e.g. follower counts) can change over time, Django Twitter stores
all of that mutable data in "snapshots" that represent what a profile
looked like at a particular point in time. Every time you collect data
on a profile - by running one of Django Twitter's data collection
commands like ``django_twitter_get_profile`` - a new record will be
created in your app's snapshot model that inherits from
``AbstractTwitterProfileSnapshot``. Snapshots are associated with their
profile through the ``snapshots`` relation:

.. code:: python

    profile = MyTwitterProfileModel.objects.get(twitter_id="12345")
    profile.snapshots.all()

And, for convenience, the most recent snapshot is also made available
directly through the ``most_recent_snapshot`` foreign key, updated each
time a new snapshot is collected:

.. code:: python

    profile.most_recent_snapshot

Followers and followings lists
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In a similar vein, Django Twitter also stores data on profiles'
followers and followings ("friends") in separate lists every time they
are collected from the API. These lists are defined by
``AbstractTwitterFollowerList`` and ``AbstractTwitterFollowingList``.
Because collecting the follower lists for extremely popular Twitter
accounts can be a hugely time-consuming process that can span hours or
even days (during which time you could encounter errors that
accidentally stop data collection prematurely), the follower and
following list models each contain a ``start_time`` and ``finish_time``
field for tracking the period during which the list was collected. In
addition to these two fields, these list objects also contain a foreign
key to the ``profile`` for whom the list was collected, and a
many-to-many relation to ``followers`` or ``followings`` containing all
of the profiles in the list.

Since this is a somewhat complicated (albeit necessary) way to store all
of this data, the ``AbstractTwitterProfile`` model provides some
shortcut functions to grab the profile's most recent lists:

.. code:: python

    profile.current_followers()
    profile.current_follower_list()
    profile.current_followings()
    profile.current_following_list()

Error codes and historical accounts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If Django Twitter encounters an error when attempting to collect a
Twitter profile, it will store the error code in the
``twitter_error_code`` field. For example, accounts that have been
suspended will return Code 63, and accounts that have been deleted by
their owner will return Code 50. Details on specific error codes can be
found in Twitter's developer documentation:
https://developer.twitter.com/ja/docs/basics/response-codes

It can often be useful to add some custom logic to your application to
determine what to do with profiles that have started to return an error
code; for example, you may want to skip data collection for deleted
accounts, etc. Django Twitter also provides a ``historical`` boolean
field on the ``AbstractTwitterProfile`` model that can be used as a
conditional flag in your app for determining whether or not to run a
data collection command for a particular profile. Django Twitter doesn't
do anything with this field itself, it exists purely as an optional
convenience for you.

Collecting Tweets and "backfilling"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can collect recent tweets for a profile (or a set of profiles) by
running the ``django_twitter_get_profile_tweets`` (or
``django_twitter_get_profile_set_tweets``) command. Django Twitter uses
Pewhooks and the Twitter v1 API to collect the tweets produced by an
account in reverse-chronological order, up to a maximum of that
profile's most recent ~3200 tweets. Doing this requires pagination to
iterate through a profile's tweet history, and each page consumes some
of your API quota - so it makes sense to only iterate through the full
list the first time you begin collecting a profile's tweets. Once you've
gone back as far as the API will allow, you're typically only interested
in keeping up with new tweets. To that end, Django Twitter sets a
``tweet_backfilled`` flag on each ``AbstractTwitterProfile`` object, to
track whether you've successfully collected all of the historically
available tweets for each profile. Once you have run
``django_twiter_get_profile_tweets`` on a profile and completed this
backfill process, Django Twitter will set the backfill flag to ``True``
and the next time you run that command, it will break off data
collection when it encounters a tweet that has already been previously
collected. To override this behavior, you can simply pass the
``--ignore-backfill`` flag to the command, or use the
``max_backfill_date`` or ``max_backfill_days`` parameters to specify how
far back you would like to go, and the ``--overwrite`` flag to specify
whether you want to update existing tweets with the latest API data. The
latter parameters can be useful if you would like to update tweets'
engagement stats (e.g. likes and retweets) for a short period of time
after they have been created - but don't want to unnecessarily iterate
through older tweets whose engagement is unlikely to have changed.

Checking tweet coverage
~~~~~~~~~~~~~~~~~~~~~~~

Depending on how often an account tweets, the ~3200 historical tweets
offered by the Twitter v1 API may provide you with years of data, or
just a mere week's worth. When analyzing a set of profiles together - as
we typically do - it's important to assess how far back your backfilling
attempts actually got for the profiles you want to analyze, and
determine the timeframe over which you actually have complete data.
Django Twitter has two utility functions to assist with this process.

The ``get_monthly_twitter_activity`` function takes a QuerySet of
profiles and a date range, and returns a Pandas DataFrame that contains
one row for each account, and columns that contain the total tweets that
exist in the database for that account in each month in your time range.
If you load this into Excel and set conditional formatting to highlight
months with low counts, it's relatively easy to tell the date ranges
that were covered by your backfilling vs. where you're missing data for
certain accounts.

.. code:: python

    from django_twitter.utils import get_monthly_twitter_activity
    df = get_monthly_twitter_activity(
        profiles,
        START_DATE,
        max_date=END_DATE,
    )
    # >>> df.head()
    #      2020_10  2020_11  2020_12  2021_1  2021_2  2021_3  2021_4  2021_5  \
    # 8.0      0.0      0.0      0.0     1.0     0.0     0.0     3.0     5.0   
    # 0.0      0.0      0.0      0.0     0.0     0.0     0.0     0.0     1.0   
    # 3.0      1.0      0.0      0.0     0.0     0.0     0.0     0.0    11.0   
    # 1.0      0.0      0.0      0.0     0.0     0.0     0.0     0.0     0.0   
    # 6.0      0.0      0.0      0.0     0.0     0.0     0.0     6.0    38.0   
    # 
    #      2021_6   pk    screen_name          created_at                     name  
    # 8.0    39.0  1.0    pewresearch 2009-03-03 10:39:39      Pew Research Center  
    # 0.0    36.0  2.0      pewglobal 2012-09-18 12:08:41      Pew Research Global  
    # 3.0    24.0  3.0     pewmethods 2015-02-09 16:00:41     Pew Research Methods  
    # 1.0    35.0  4.0  pewjournalism 2010-02-04 09:42:57  Pew Research Journalism  
    # 6.0     2.0  5.0       facttank 2013-03-13 18:41:33   Pew Research Fact Tank 

The ``find_missing_date_ranges`` gives you a slightly different view of
your missing data, intended to highlight periods where there may be
unnatural gaps in the timeseries (i.e. due to data collection failure,
etc.) This function returns a dataframe that lists time periods longer
than ``min_consecutive_missing_dates`` where no tweets exist for a
particular account in the database.

.. code:: python

    from django_twitter.utils import find_missing_date_ranges
    results = find_missing_date_ranges(
        profiles,
        START_DATE,
        max_date=END_DATE,
        min_consecutive_missing_dates=5,
    )
    # >>> results.head()
    #     twitter_id  start_date    end_date  range
    # 3    111339670  2021-01-01  2021-06-07    157
    # 11  1262729180  2021-01-01  2021-05-27    146
    # 28    17071048  2021-01-01  2021-05-21    140
    # 0    831470472  2021-01-01  2021-05-19    138
    # 12    36462231  2021-01-01  2021-05-18    137

Streaming API
~~~~~~~~~~~~~

TODO

Exporting data
~~~~~~~~~~~~~~

TODO: get\_tweet\_dataframe

Since we often conduct research on tweets as well as profile attributes,
and want to capture a representation of each tweet's authoring profile
*as it existed at the time of the tweet*, Django Twitter also provides a
handy functions for extracting a Pandas DataFrame of a profile's
snapshots over a particular timeframe. This function has support for
linear interpolation, so you can approximate and fill in gaps for days
where you didn't collect any profile data.

.. code:: python

    START_DATE = datetime.date(2021, 1, 1)
    END_DATE = datetime.date(2021, 1, 31)
    df = profile.get_snapshots(
        START_DATE,
        END_DATE,
        skip_interpolation=False
    )

You can also fetch a snapshot dataframe for multiple profiles using the
``get_twitter_profile_dataframe`` utility function:

.. code:: python

    from django_twitter.utils import get_twitter_profile_dataframe
    df = get_twitter_profile_dataframe(
        profiles, # a QuerySet of Twitter profiles
        START_DATE,
        END_DATE, 
        skip_interpolation=False
    )

