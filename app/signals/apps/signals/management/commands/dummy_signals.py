# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
from django.core.management import BaseCommand

from signals.apps.signals.factories import SignalFactory
from signals.apps.signals.models import Category


class Command(BaseCommand):
    default_to_create = 100
    min_to_create = 1
    max_to_create = 1000

    def add_arguments(self, parser):
        parser.add_argument('--to-create', type=int, help=f'Total random Signals to create (max {self.max_to_create}). '
                                                          f'Default {self.default_to_create}.')

    def handle(self, *args, **options):
        to_create = int(options['to_create'] or self.default_to_create)
        if not self.min_to_create <= to_create <= self.max_to_create:
            self.stderr.write(f'The to create option must be an integer from {self.min_to_create} to '
                              f'{self.max_to_create}, {to_create} given')
        else:
            # We also need to perform some checks and determine a category to create Signals in
            category_qs = Category.objects.filter(parent__isnull=False, is_active=True)
            if category_qs.count() == 0:
                self.stderr.write('Create some categories first')
            else:
                for _ in range(to_create):
                    random_category = category_qs.order_by('?').first()
                    SignalFactory.create(category_assignment__category=random_category)
                self.stdout.write(f'Created {to_create} random Signal(s)')
