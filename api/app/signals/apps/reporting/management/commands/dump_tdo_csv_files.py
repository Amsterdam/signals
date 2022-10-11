# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2022 Gemeente Amsterdam
from timeit import default_timer as timer

from django.conf import settings
from django.core.management import BaseCommand
from django.utils import timezone

from signals.apps.reporting.csv.tdo import (
    create_signals_csv,
    create_statuses_csv,
    save_csv_file_tdo
)

REPORT_OPTIONS = {
    'signals': create_signals_csv,
    'statuses': create_statuses_csv,
}


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--report', type=str,
                            help=f'Report type to export (if none given all reports will be exported), '
                                 f'choices are: {", ".join(REPORT_OPTIONS.keys())}')

    def handle(self, *args, **kwargs):
        start = timer()

        if settings.AZURE_STORAGE_ENABLED:
            self.stdout.write('Azure storage: Enabled')
            azure_parameters = settings.AZURE_CONTAINERS.get('datawarehouse')
            self.stdout.write(f'* Azure storage container name: {azure_parameters["azure_container"]}')
        elif settings.SWIFT_STORAGE_ENABLED:
            self.stdout.write('Swift storage: Enabled')
            swift_parameters = settings.SWIFT.get('datawarehouse')
            self.stdout.write(f'* Swift storage container name: {swift_parameters["container_name"]}')
        else:
            now = timezone.now()
            self.stdout.write('Local file storage: Enabled')
            self.stdout.write(f'* Local File storage directory: {now:%Y}/{now:%m}/{now:%d}/')

        reports = kwargs['report'].split(',') if kwargs['report'] else None
        if reports is None or set(reports) == set(REPORT_OPTIONS.keys()):
            reports = REPORT_OPTIONS.keys()

        reports = set(reports)
        self.stdout.write(f'Export: {", ".join(reports)}')
        for report in reports:
            self.stdout.write(f'* Exporting: {report}')
            func = REPORT_OPTIONS[report]
            save_csv_file_tdo(func)
            self.stdout.write('* ---------------------------------')

        stop = timer()
        self.stdout.write(f'Time: {stop - start:.2f} second(s)')
        self.stdout.write('Done!')
