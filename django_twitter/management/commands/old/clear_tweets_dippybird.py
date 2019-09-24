from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from pewtils.io import FileHandler

from dippybird.models import Tweet, Link


class Command(BaseCommand):
    def handle(self, *args, **options):

        # h = FileHandler("tweets", bucket=settings.AWS_STORAGE_BUCKET_NAME, use_s3=True)
        # h.clear_folder()

        Tweet.objects.all().chunk_delete(1000)
