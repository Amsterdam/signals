# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
from django.core.management import BaseCommand

from signals.apps.reporting.services.clean_up_datawarehouse import DataWarehouseDiskCleaner
from signals.apps.reporting.utils import _get_storage_backend


class Command(BaseCommand):
    def add_arguments(self, parser) -> None:
        parser.add_argument('--keep-n-days', dest='keep_n_days', type=int, default=30,
                            help='Number of days to retain data for.')
        parser.add_argument('--dry-run', dest='dry_run', action='store_true', default=False,
                            help='Perform dry run without deleting data files.')

    def handle(self, *args, **options):
        self.stdout.write('Cleaning up local disk by removing old CSV exports.')
        storage = _get_storage_backend(using='datawarehouse')
        self.stdout.write(f'\nStorage location: {storage.location}\n')
        scanned, removed = DataWarehouseDiskCleaner.clean_up(
            storage.location, keep_n_days=options['keep_n_days'], dry_run=options['dry_run'])

        self.stdout.write('\nScanned following locations:\n')
        for path in scanned:
            self.stdout.write(f'{path}\n')
        self.stdout.write('\nRemoved following files:\n')
        for path in removed:
            self.stdout.write(f'{path}\n')

        self.stdout.write(f'\nA total of {len(removed)} files were removed.')
