# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
import uuid

from django.core.management import BaseCommand
from django.db import DatabaseError, transaction
from django.utils import timezone

from signals.apps.services.domain.delete_signals import SignalDeletionService
from signals.apps.signals.models import DeletedSignal
from signals.apps.signals.workflow import AFGEHANDELD, GEANNULEERD, GESPLITST


class Command(BaseCommand):
    STATE_CHOICES = (AFGEHANDELD, GEANNULEERD, GESPLITST, )
    _dry_run = False

    def add_arguments(self, parser):
        parser.add_argument('state', type=str, help='State a Signal must be in to be deleted'
                                                    f'choices are: {", ".join(self.STATE_CHOICES)}')
        parser.add_argument('days', type=int, help='Minimum days a Signal must be in the given state to be deleted')

        parser.add_argument('--signal-id', type=int, dest='signal_id', help='The ID of a Signal to delete. Only '
                                                                            'accepts normal signals or parent signals')

        parser.add_argument('--dry-run', action='store_true', dest='_dry_run', help='Dry-run mode, will not delete any '
                                                                                    'signals')

    def _pre_handle(self, **options):
        """
        Check if all given options are valid
        """
        self.state = options['state']
        self.days = options['days']
        self.signal_id = options['signal_id'] or None
        SignalDeletionService().check_preconditions(self.state, self.days, self.signal_id)

        self._dry_run = options['_dry_run']
        self.batch_uuid = uuid.uuid4()
        self.now = timezone.now()

    def handle(self, *args, **options):
        try:
            self._pre_handle(**options)
        except ValueError as e:
            self.stderr.write(f'{e}')
            return

        self.write_start_msg()

        signal_qs = SignalDeletionService().get_queryset_for_deletion(self.state, self.days, self.signal_id)
        if signal_qs.exists():
            try:
                with transaction.atomic():
                    deleted_signals = SignalDeletionService().delete_queryset(signal_qs, self.batch_uuid, self._dry_run)
            except DatabaseError:
                pass
            else:
                # Transaction was not rolled back
                self.list_deleted_signals(deleted_signals)
        else:
            self.stdout.write('No signal(s) found that matches criteria')

        self.write_end_msg()

    def list_deleted_signals(self, deleted_signals):
        for signal_id in deleted_signals:
            self.stdout.write(f'Deleted Signal: #{signal_id}{" (dry-run)" if self._dry_run else ""}')

    def write_start_msg(self):
        if self._dry_run:
            self.stdout.write('Dry-run mode: Enabled')

        self.stdout.write(f'Started: {self.now:%Y-%m-%d %H:%M:%S}')
        self.stdout.write(f'Batch UUID: {self.batch_uuid}')
        self.stdout.write(f'State: {self.state}')
        self.stdout.write(f'Days: {self.days}')
        if self.signal_id:
            self.stdout.write(f'Signal ID: {self.signal_id}')
        self.stdout.write(f'{"":-<80}')

    def write_end_msg(self):
        self.stdout.write(f'{"":-<80}')
        if self._dry_run:
            self.stdout.write('Dry-run mode: Enabled')
        ds_qs = DeletedSignal.objects.filter(batch_uuid=self.batch_uuid)
        self.stdout.write(f'Deleted: {ds_qs.count()} Signal(s)')
        self.stdout.write(f'{"":-<80}')
        self.stdout.write(f'Done: {timezone.now():%Y-%m-%d %H:%M:%S}')
