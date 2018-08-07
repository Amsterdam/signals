from django.core.management import BaseCommand, CommandError
from signals.models import *


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        models = [Signal, Location, Reporter, Status, Category]

        for m in models:
            m.objects.all().delete()


