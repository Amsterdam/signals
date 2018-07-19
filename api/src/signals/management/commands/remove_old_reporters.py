from django.core.management import BaseCommand

from signals.tasks.remove_old_reporters import remove_old_reporters


class Command(BaseCommand):
    def handle(self, *args, **options):
        remove_old_reporters()