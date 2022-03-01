import os
import copy
from django.apps import AppConfig


class DjangoTwitterConfig(AppConfig):
    name = "django_twitter"

    def update_settings(self):

        from django.conf import settings

        if settings.TWITTER_APP != "django_twitter":
            migrations = copy.deepcopy(settings.MIGRATION_MODULES)
            migrations["django_twitter"] = None
            setattr(settings, "MIGRATION_MODULES", migrations)

    def __init__(self, *args, **kwargs):
        super(DjangoTwitterConfig, self).__init__(*args, **kwargs)
        self.update_settings()

    def ready(self):
        self.update_settings()
