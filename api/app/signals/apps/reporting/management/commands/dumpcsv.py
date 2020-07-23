import os
from timeit import default_timer as timer

from django.core.management import BaseCommand
from django.utils import timezone

from signals.apps.reporting.csv.datawarehouse import get_swift_parameters
from signals.apps.reporting.csv.datawarehouse.categories import (
    create_category_assignments_csv,
    create_category_sla_csv
)
from signals.apps.reporting.csv.datawarehouse.kto_feedback import create_kto_feedback_csv
from signals.apps.reporting.csv.datawarehouse.locations import create_locations_csv
from signals.apps.reporting.csv.datawarehouse.reporters import create_reporters_csv
from signals.apps.reporting.csv.datawarehouse.signals import create_signals_csv
from signals.apps.reporting.csv.datawarehouse.statusses import create_statuses_csv
from signals.apps.reporting.csv.datawarehouse.tasks import save_csv_file_datawarehouse

REPORT_OPTIONS = {
    # Option, Func
    'signals': create_signals_csv,
    'locations': create_locations_csv,
    'reporters': create_reporters_csv,
    'category_assignments': create_category_assignments_csv,
    'statusses': create_statuses_csv,
    'category_sla': create_category_sla_csv,
    'feedback': create_kto_feedback_csv,
}


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--report', type=str,
                            help=f'Report type to export (if none given all reports will be exported), '
                                 f'choices are: {", ".join(REPORT_OPTIONS.keys())}')

    def handle(self, *args, **kwargs):
        start = timer()

        swift_enabled = os.getenv('SWIFT_ENABLED', False) in [True, 1, '1', 'True', 'true']
        self.stdout.write('Swift storage: '
                          f'{"Enabled" if swift_enabled else "Disabled (Files will be stored in local file storage"}')
        if swift_enabled:
            swift_parameters = get_swift_parameters()
            self.stdout.write(f'* Swift storage container name: {swift_parameters["container_name"]}')
        else:
            now = timezone.now()
            self.stdout.write(f'* Local File storage directory: {now:%Y}/{now:%m}/{now:%d}/')

        reports = kwargs['report'].split(',') if kwargs['report'] else None
        if reports is None or set(reports) == set(REPORT_OPTIONS.keys()):
            reports = REPORT_OPTIONS.keys()

        reports = set(reports)
        self.stdout.write(f'Export: {", ".join(reports)}')
        for report in reports:
            self.stdout.write(f'* Exporting: {report}')
            func = REPORT_OPTIONS[report]
            save_csv_file_datawarehouse(func)
            self.stdout.write('* ---------------------------------')

        stop = timer()
        self.stdout.write(f'Time: {stop - start:.2f} second(s)')
        self.stdout.write('Done!')
