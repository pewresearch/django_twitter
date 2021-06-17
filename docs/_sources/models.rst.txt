*************************************
django_twitter.models
*************************************

Django Twitter provides a series of abstract models to store data from the Twitter API. If you
import these abstract classes and your own app's models inherit from them, Django Twitter will
automatically create a standard set of model fields and relations for you.

Base models
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. autoclass :: django_twitter.models.AbstractTwitterBase
  :members: __new__

.. autoclass :: django_twitter.models.AbstractTwitterObject
  :members: save

Twitter profiles and snapshots
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. autoclass :: django_twitter.models.AbstractTwitterProfile
  :members: save, url, get_snapshots, current_followers, current_follower_list, current_followings, current_following_list

.. autoclass :: django_twitter.models.AbstractTwitterProfileSnapshot
  :members: update_from_json, url

Tweets
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. autoclass :: django_twitter.models.AbstractTweet
  :members: update_from_json, url

Followers and followings lists
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. autoclass :: django_twitter.models.AbstractTwitterFollowerList

.. autoclass :: django_twitter.models.AbstractTwitterFollowingList

Tweet and profile sets
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. autoclass :: django_twitter.models.AbstractTweetSet

.. autoclass :: django_twitter.models.AbstractTwitterProfileSet

Other objects
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. autoclass :: django_twitter.models.AbstractTwitterHashtag
  :members: save

.. autoclass :: django_twitter.models.AbstractTwitterPlace
  :members: save


