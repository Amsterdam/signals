# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 - 2023 Gemeente Amsterdam
from django.core.management import BaseCommand
from django.utils import timezone

from signals.apps.services.domain.signals.delete import DeleteSignalsService
from signals.apps.signals.models import DeletedSignal


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('state',
                            type=str,
                            help='State a Signal must be in to be deleted'
                                 f'choices are: {", ".join(DeleteSignalsService.valid_states)}')
        parser.add_argument('days',
                            type=int,
                            help='Minimum days a Signal must be in the given state to be deleted')
        parser.add_argument('--dry-run',
                            action='store_true',
                            dest='_dry_run',
                            help='Dry-run mode, will not delete any signals')

    def handle(self, *args, **options):
        state = options['state']
        days = options['days']
        dry_run = options['_dry_run']

        if dry_run:
            self.stdout.write('Dry-run mode: Enabled')

        self.stdout.write(f'Started: {timezone.now():%Y-%m-%d %H:%M:%S}')
        self.stdout.write(f'{"":-<80}')
        self.stdout.write(f'State: {state}')
        self.stdout.write(f'Days: {days}')

        try:
            batch_uuid = DeleteSignalsService.run(state=state, days=days, delay_deletion=False, dry_run=dry_run)
        except ValueError as e:
            self.stderr.write(f'{e}')
            return

        ds_qs = DeletedSignal.objects.filter(batch_uuid=batch_uuid)
        self.stdout.write(f'Deleted: {ds_qs.count()} Signal(s)')

        if ds_qs.exists():
            self.stdout.write(f'{"":-<80}')
            for signal_id in ds_qs.values_list('signal_id', flat=True):
                self.stdout.write(f'Deleted Signal: #{signal_id}')

        self.stdout.write(f'{"":-<80}')
        self.stdout.write(f'Done: {timezone.now():%Y-%m-%d %H:%M:%S}')
