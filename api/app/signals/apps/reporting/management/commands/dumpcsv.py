from timeit import default_timer as timer

from django.core.management import BaseCommand

from signals.apps.reporting.csv.datawarehouse.categories import (
    create_category_assignments_csv,
    create_category_sla_csv
)
from signals.apps.reporting.csv.datawarehouse.kto_feedback import create_kto_feedback_csv
from signals.apps.reporting.csv.datawarehouse.locations import create_locations_csv
from signals.apps.reporting.csv.datawarehouse.reporters import create_reporters_csv
from signals.apps.reporting.csv.datawarehouse.signals import create_signals_csv
from signals.apps.reporting.csv.datawarehouse.statusses import create_statuses_csv
from signals.apps.reporting.csv.datawarehouse.tasks import (
    save_csv_file_datawarehouse,
    save_csv_files_datawarehouse
)

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

        reports = kwargs['report'].split(',') if kwargs['report'] else None
        if reports is None or set(reports) == set(REPORT_OPTIONS.keys()):
            # Default is to export all, if all options are selected also export all
            self.stdout.write(f'Export: {", ".join(REPORT_OPTIONS.keys())}')
            self._dump_all()
        else:
            # Only export the selected reports
            reports = set(reports)
            self.stdout.write(f'Export: {", ".join(reports)}')
            for report in reports:
                self._dump_selected(report)

        stop = timer()
        self.stdout.write(f'Time: {stop - start:.2f} second(s)')
        self.stdout.write('Done!')

    def _dump_all(self):
        save_csv_files_datawarehouse()

    def _dump_selected(self, report):
        func = REPORT_OPTIONS[report]
        save_csv_file_datawarehouse(func)
