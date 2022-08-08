# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
import os
from timeit import default_timer as timer

from django.conf import settings
from django.core.management import BaseCommand
from django.utils import timezone
from django.conf import settings
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

        self.stdout.write('Azure storage: '
                          f'{"Enabled" if settings.AZURE_ENABLED else "Disabled (Files will be stored in local file storage"}')
        if settings.AZURE_ENABLED:
            azure_parameters = settings.AZURE_CONTAINERS.get('tdo')
            self.stdout.write(f'* Azure storage container name: {azure_parameters["azure_container"]}')
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
            save_csv_file_tdo(func)
            self.stdout.write('* ---------------------------------')

        stop = timer()
        self.stdout.write(f'Time: {stop - start:.2f} second(s)')
        self.stdout.write('Done!')
