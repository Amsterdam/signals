# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
from django.core.management import BaseCommand

from signals.apps.signals.factories import DepartmentFactory


class Command(BaseCommand):
    default_to_create = 1
    min_to_create = 1
    max_to_create = 10

    def add_arguments(self, parser):
        parser.add_argument('--to-create', type=int, help='Total random Departments to create '
                                                          f'(max {self.max_to_create}). '
                                                          f'Default {self.default_to_create}.')

    def handle(self, *args, **options):
        to_create = int(options['to_create'] or self.default_to_create)
        if not self.min_to_create <= to_create <= self.max_to_create:
            self.stderr.write(f'The to create option must be an integer from {self.min_to_create} to '
                              f'{self.max_to_create}, {to_create} given')
        else:
            DepartmentFactory.create_batch(to_create)
            self.stdout.write(f'Created {to_create} random Department(s)')
