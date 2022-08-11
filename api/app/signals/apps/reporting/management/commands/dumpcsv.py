# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from timeit import default_timer as timer

from django.conf import settings
from django.core.management import BaseCommand
from django.utils import timezone

from signals.apps.reporting.csv.datawarehouse.categories import (
    create_category_assignments_csv,
    create_category_sla_csv
)
from signals.apps.reporting.csv.datawarehouse.directing_departments import (
    create_directing_departments_csv
)
from signals.apps.reporting.csv.datawarehouse.kto_feedback import create_kto_feedback_csv
from signals.apps.reporting.csv.datawarehouse.locations import create_locations_csv
from signals.apps.reporting.csv.datawarehouse.reporters import create_reporters_csv
from signals.apps.reporting.csv.datawarehouse.signals import (
    create_signals_assigned_user_csv,
    create_signals_csv,
    create_signals_notes_csv,
    create_signals_routing_departments_csv
)
from signals.apps.reporting.csv.datawarehouse.statusses import create_statuses_csv
from signals.apps.reporting.csv.datawarehouse.tasks import (
    save_csv_file_datawarehouse,
    zip_csv_files_endpoint
)

REPORT_OPTIONS = {
    # Option, Func
    'signals': create_signals_csv,
    'signals_assigned_user': create_signals_assigned_user_csv,
    'locations': create_locations_csv,
    'reporters': create_reporters_csv,
    'category_assignments': create_category_assignments_csv,
    'statusses': create_statuses_csv,
    'category_sla': create_category_sla_csv,
    'feedback': create_kto_feedback_csv,
    'directing_departments': create_directing_departments_csv,
    'routing_departments': create_signals_routing_departments_csv,
    'notes': create_signals_notes_csv
}


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--report', type=str,
                            help=f'Report type to export (if none given all reports will be exported), '
                                 f'choices are: {", ".join(REPORT_OPTIONS.keys())}')
        parser.add_argument("--zip", action="store_true", dest='zip', help="Also output zip file.")

    def handle(self, *args, **kwargs):
        start = timer()

        self.stdout.write('Azure storage: '
                          f'{"Enabled" if settings.AZURE_ENABLED else "Disabled (Files will be stored in local file storage"}') # noqa
        if settings.AZURE_ENABLED:
            azure_parameters = settings.AZURE_CONTAINERS.get('datawarehouse')
            self.stdout.write(f'* Azure storage container name: {azure_parameters["azure_container"]}')
        else:
            now = timezone.now()
            self.stdout.write(f'* Local File storage directory: {now:%Y}/{now:%m}/{now:%d}/')

        reports = kwargs['report'].split(',') if kwargs['report'] else None
        if reports is None or set(reports) == set(REPORT_OPTIONS.keys()):
            reports = REPORT_OPTIONS.keys()

        reports = set(reports)
        self.stdout.write(f'Export: {", ".join(reports)}')
        csv_files = list()
        for report in reports:
            self.stdout.write(f'* Exporting: {report}')
            func = REPORT_OPTIONS[report]
            csv_files.extend(save_csv_file_datawarehouse(func))
            self.stdout.write('* ---------------------------------')

        if kwargs['zip']:
            self.stdout.write('* Making zipfile...')
            zip_csv_files_endpoint(files=csv_files)
            self.stdout.write('* ---------------------------------')
        stop = timer()
        self.stdout.write(f'Time: {stop - start:.2f} second(s)')
        self.stdout.write('Done!')
