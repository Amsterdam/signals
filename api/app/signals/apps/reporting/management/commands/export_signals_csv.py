"""
Export specified signals to CSV.
"""
import logging
import re
import pprint

from django.core.management import BaseCommand

from signals.apps.reporting.models import CSVExport

logger = logging.getLogger(__name__)


def convert_categories(s):
    """
    expected input
    [[<main_slug>,<sub_slug>],...]

    output
    [{"main_slug": <main_slug>, "sub_slug": <sub_slug>}, ...]
    """
    cat_pattern = r'\[(?P<main_slug>[\w-]+),(?P<sub_slug>[\w-]+)\]'
    potential_categories = s.strip()[1:-1]

    output_categories = []
    for match in re.finditer(cat_pattern, potential_categories):
        output_categories.append({
            'main_slug': match.group('main_slug'),
            'sub_slug': match.group('sub_slug')
        })
    return output_categories


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--isoweek', type=int)
        parser.add_argument('--isoyear', type=int)
        parser.add_argument('--year', type=int)
        parser.add_argument('--month', type=int)
        parser.add_argument('--day', type=int)
        parser.add_argument('--categories', type=str)
        parser.add_argument('basename', type=str)

    def handle(self, *args, **options):
        self.stdout.write('Starting Signals CSV export ...')

        export_parameters = {}
        for option, value in options.items():
            if option not in ['isoweek', 'isoyear', 'year', 'month', 'day', 'categories']:
                continue
            elif value is not None and option == 'categories':
                export_parameters['categories'] = convert_categories(options['categories'])
            elif value is not None:
                export_parameters[option] = value
        s = pprint.pformat(export_parameters)

        self.stdout.write(s)

        csv_export = CSVExport.objects.create_csv_export(options['basename'], export_parameters)

        self.stdout.write('... done')
