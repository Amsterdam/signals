# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
import uuid

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.management import BaseCommand
from django.db import transaction
from django.utils import timezone

from signals.apps.search.tasks import delete_from_elastic
from signals.apps.signals.models import DeletedSignal, Signal
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
        if not settings.FEATURE_FLAGS.get('DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED', False):
            raise ValueError('Feature flag "DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED" is not enabled')

        if options['state'] not in self.STATE_CHOICES:
            raise ValueError(f'Invalid state(s) provided must be one of "{", ".join(self.STATE_CHOICES)}"')
        self.state = options['state']

        if options['days'] < 365:
            raise ValueError('Invalid days provided must be at least 365')
        self.days = options['days']

        if options['signal_id'] and not Signal.objects.filter(id=options['signal_id'], parent_id__isnull=True).exists():
            raise ValueError(f'Invalid signal_id provided, no (parent) Signal with id "{options["signal_id"]}" exists')
        self.signal_id = options['signal_id'] or None

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

        signal_qs = self._select_signals()
        if signal_qs.exists():
            with transaction.atomic():
                self._loop_through_signals(signal_qs=signal_qs)
        else:
            self.stdout.write('No signal(s) found that matches criteria')

        self.write_end_msg()

    def _select_signals(self):
        # Select Signals that are in the given states and the state has been set more than X days ago
        # Only select normal signals or parent signals
        queryset = Signal.objects.filter(parent_id__isnull=True, status__state=self.state,
                                         status__created_at__lt=timezone.now() - timezone.timedelta(days=self.days))

        if self.signal_id:
            # A specific Signal ID was given, only select that Signal
            queryset = queryset.filter(id=self.signal_id)

        return queryset

    def _loop_through_signals(self, signal_qs):
        for signal in signal_qs:
            if signal.is_parent:
                # First delete all child Signals
                self._loop_through_signals(signal_qs=signal.children.all())

            # Delete the Signal
            self._delete_signal(signal=signal)

    def _delete_signal(self, signal):
        """
        Deletes the given signal and all related objects. Will also remove the Signal from the elasticsearch index.
        """
        signal_id = signal.id
        if not self._dry_run:
            # Meta data needed for reporting
            DeletedSignal.objects.create_from_signal(
                signal=signal,
                action='automatic',
                note=self.get_log_note(signal),
                batch_uuid=self.batch_uuid
            )

            attachment_files = [attachment.file.path for attachment in signal.attachments.all()]
            signal.attachments.all().delete()

            try:
                delete_from_elastic(signal=signal)
            except Exception:
                pass

            signal.delete()

            for attachment_file in attachment_files:
                if default_storage.exists(attachment_file):
                    default_storage.delete(attachment_file)

        self.stdout.write(f'Deleted Signal: #{signal_id}{" (dry-run)" if self._dry_run else ""}')

    # Helper functions

    def get_log_note(self, signal):
        diff = timezone.now() - signal.status.created_at
        if signal.is_child:
            diff = timezone.now() - signal.parent.status.created_at
            return f'Parent signal was in state "{signal.parent.status.get_state_display()}" for {diff.days} days'
        return f'signal was in state "{signal.status.get_state_display()}" for {diff.days} days'

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
