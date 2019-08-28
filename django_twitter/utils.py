from django.conf import settings
from django.apps import apps


def get_twitter_user(twitter_id, twitter_handler):

    user_model = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWITTER_PROFILE_MODEL)
    twitter_json = twitter_handler.get_user(twitter_id, return_errors=True)
    if isinstance(twitter_json, int):
        error_code = twitter_json
        try:
            existing_profile = user_model.objects.get(twitter_id=twitter_id)
        except user_model.DoesNotExist:
            existing_profile = None
        except user_model.MultipleObjectsReturned:
            print("Warning: multiple users found for {}".format(twitter_id))
            print("For flexibility, Django Twitter does not enforce a unique constraint on twitter_id")
            print("But in this case it can't tell which user to use, so it's picking the most recently updated one")
            existing_profile = user_model.objects.filter(twitter_id=twitter_id).order_by("-last_update_time")[0]
        if existing_profile:
            existing_profile.twitter_error_code = error_code
            existing_profile.save()
        return None
    else:
        return twitter_json