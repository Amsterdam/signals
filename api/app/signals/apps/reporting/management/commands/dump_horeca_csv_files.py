import logging

from django.core.exceptions import ValidationError
from django.core.management import BaseCommand

from signals.apps.reporting.csv.horeca import create_csv_files

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('isoweek', type=int)
        parser.add_argument('isoyear', type=int)

    def _validate_arguments(self, options):
        logger.info('Validate given arguments')
        if options['isoweek'] and (options['isoweek'] < 1 or options['isoweek'] > 53):
            raise ValidationError('Given week must be between 0 or 53')

    def handle(self, *args, **options):
        logger.info('Dump Horeca CSV files per sub category')

        self._validate_arguments(options)

        csv_files = create_csv_files(isoweek=options['isoweek'],
                                     isoyear=options['isoyear'])

        for csv_file in csv_files:
            logger.info('Created file "{}"'.format(csv_file))
