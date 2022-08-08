# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
import csv
import os
from timeit import default_timer as timer

from django.conf import settings
from django.core.management import BaseCommand
from django.utils import timezone
from django.conf import settings

from signals.apps.reporting.csv.datawarehouse import save_csv_file_datawarehouse


def _test_file(tmp_dir: str) -> str:

    now = timezone.now()
    csv_file_path = os.path.join(tmp_dir, f'{now:%Y}-{now:%m}-{now:%d}_{now:%H%M%S%Z}_test.csv')
    with open(csv_file_path, 'w') as file:
        writer = csv.DictWriter(file, fieldnames=['header-1', 'header-2', 'header-3'])
        writer.writeheader()
        writer.writerow({'header-1': 'value-1', 'header-2': 'value-2', 'header-3': 'value-3'})
    return file.name


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        start = timer()
        self.stdout.write('Store a test CSV file')

        very_verbose = kwargs['verbosity'] >= 2

        if settings.AZURE_ENABLED:
            self.stdout.write('* AzureStorage enabled, file will be sent to the ObjectStore')
        else:
            self.stdout.write('* FileSystemStorage enabled, file will be sent to the local storage')

        if settings.AZURE_ENABLED and very_verbose:
            azure_parameters = settings.AZURE_CONTAINERS.get('datawarehouse')
            self.stdout.write('* DWH AzureStorage parameters:')

            for key, value in azure_parameters.items():
                if key.lower() in ['api_key', ]:
                    continue

                self.stdout.write(f'** {key}: {value}')

        self.stdout.write('* Create CSV')
        save_csv_file_datawarehouse(_test_file)

        stop = timer()
        self.stdout.write(f'Time: {stop - start:.2f} second(s)')
        self.stdout.write('Done!')
