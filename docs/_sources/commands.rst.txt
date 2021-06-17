*************************************
django_twitter.management.commands
*************************************

Django Twitter provides a series of management commands for collecting and storing data from the Twitter API,
which you can run via the CLI or by using Django's `call_command` function.

Streaming API
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

django_twitter_collect_tweet_stream
""""""""""""""""""""""""""""""""""""""""
.. autoclass :: django_twitter.management.commands.django_twitter_collect_tweet_stream.Command
  :autosummary:

Collecting profile data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

django_twitter_get_profile
""""""""""""""""""""""""""""""""""""""""
.. autoclass :: django_twitter.management.commands.django_twitter_get_profile.Command
  :autosummary:

django_twitter_get_profile_set
""""""""""""""""""""""""""""""""""""""""
.. autoclass :: django_twitter.management.commands.django_twitter_get_profile_set.Command
  :autosummary:

Collecting tweets
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

django_twitter_get_profile_tweets
""""""""""""""""""""""""""""""""""""""""
.. autoclass :: django_twitter.management.commands.django_twitter_get_profile_tweets.Command
  :autosummary:

django_twitter_get_profile_set_tweets
""""""""""""""""""""""""""""""""""""""""
.. autoclass :: django_twitter.management.commands.django_twitter_get_profile_set_tweets.Command
  :autosummary:

Collecting followers and followings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

django_twitter_get_profile_followers
""""""""""""""""""""""""""""""""""""""""
.. autoclass :: django_twitter.management.commands.django_twitter_get_profile_followers.Command
  :autosummary:

django_twitter_get_profile_followings
""""""""""""""""""""""""""""""""""""""""
.. autoclass :: django_twitter.management.commands.django_twitter_get_profile_followings.Command
  :autosummary:

django_twitter_get_profile_set_followers
""""""""""""""""""""""""""""""""""""""""
.. autoclass :: django_twitter.management.commands.django_twitter_get_profile_set_followers.Command
  :autosummary:

django_twitter_get_profile_set_followings
""""""""""""""""""""""""""""""""""""""""""
.. autoclass :: django_twitter.management.commands.django_twitter_get_profile_set_followings.Command
  :autosummary: