from django.core.management.base import BaseCommand, CommandError

from signals.apps.classification.models import TrainingSet
from signals.apps.classification.tasks import train_classifier

class Command(BaseCommand):
    help = "Train specific model"

    def add_arguments(self, parser):
        parser.add_argument("training_set_id", type=int)

    def handle(self, *args, **options):
        try:
            training_set = TrainingSet.objects.get(pk=options["training_set_id"])
        except TrainingSet.DoesNotExist:
            raise CommandError('Training Set "%s" does not exist' % options["training_set_id"])

        train_classifier(training_set.id)

