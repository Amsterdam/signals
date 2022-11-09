# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
import uuid

from django.conf import settings
from django.core.files.storage import default_storage
from django.db import transaction
from django.utils import timezone

from signals.apps.search.tasks import delete_from_elastic
from signals.apps.signals.models import DeletedSignal, Signal
from signals.apps.signals.workflow import AFGEHANDELD, GEANNULEERD, GESPLITST


class SignalDeletionService:
    STATE_CHOICES = (AFGEHANDELD, GEANNULEERD, GESPLITST, )

    @staticmethod
    def delete_signals(state, days, signal_id=None, dry_run=True):
        """
        Delete signals and child signals in given state and older than some number of days.
        """
        start_time = timezone.now()
        SignalDeletionService.check_preconditions(state, days, signal_id)  # May raise a ValueError

        batch_uuid = uuid.uuid4()

        signal_qs = SignalDeletionService.get_queryset_for_deletion(state, days)

        if signal_qs.exists():
            with transaction.atomic():
                SignalDeletionService.delete_queryset(signal_qs, batch_uuid, dry_run)

        ds_qs = DeletedSignal.objects.filter(batch_uuid=batch_uuid)

        return ds_qs.count(), batch_uuid, timezone.now() - start_time

    @staticmethod
    def check_preconditions(state, days, signal_id):
        """
        Check if all given options are valid
        """
        if not settings.FEATURE_FLAGS.get('DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED', False):
            raise ValueError('Feature flag "DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED" is not enabled')

        if state not in SignalDeletionService.STATE_CHOICES:
            raise ValueError(f'Invalid state(s) provided must be one of "{", ".join(SignalDeletionService.STATE_CHOICES)}"')  # noqa

        if days < 365:
            raise ValueError('Invalid days provided must be at least 365')

        if signal_id and not Signal.objects.filter(id=signal_id, parent_id__isnull=True).exists():
            raise ValueError(f'Invalid signal_id provided, no (parent) Signal with id "{signal_id}" exists')

    @staticmethod
    def get_queryset_for_deletion(state, days, signal_id=None):
        """
        Select signals for deletion.

        Selected signals are in given state and older than some number of days.
        """
        # Select Signals that are in the given states and the state has been set more than X days ago
        # Only select normal signals or parent signals
        queryset = Signal.objects.filter(parent_id__isnull=True, status__state=state,
                                         status__created_at__lt=timezone.now() - timezone.timedelta(days=days))

        if signal_id:
            # A specific Signal ID was given, only select that Signal
            queryset = queryset.filter(id=signal_id)

        return queryset

    @staticmethod
    def delete_queryset(signal_qs, batch_uuid, dry_run):
        """
        Delete all signals and child signals included in given queryset
        """
        deleted_signals = []
        for signal in signal_qs:
            signal_id = signal.id
            if signal.is_parent:
                # First delete all child Signals
                deleted_children = SignalDeletionService.delete_queryset(signal.children.all(), batch_uuid, dry_run)
                deleted_signals.extend(deleted_children)

            # Delete the Signal
            SignalDeletionService._delete_signal(signal, batch_uuid, dry_run)
            deleted_signals.append(signal_id)

        return deleted_signals

    @staticmethod
    def _delete_signal(signal, batch_uuid, dry_run):
        """
        Deletes the given signal and all related objects. Will also remove the Signal from the elasticsearch index.
        """
        if not dry_run:
            # Meta data needed for reporting
            DeletedSignal.objects.create_from_signal(
                signal=signal,
                action='automatic',
                note=SignalDeletionService.get_log_note(signal),
                batch_uuid=batch_uuid
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

    @staticmethod
    def get_log_note(signal):
        """
        Get log note for DeletedSignal instance
        """
        now = timezone.now()
        diff = now - signal.status.created_at
        if signal.is_child:
            diff = now - signal.parent.status.created_at
            return f'Parent signal was in state "{signal.parent.status.get_state_display()}" for {diff.days} days'
        return f'signal was in state "{signal.status.get_state_display()}" for {diff.days} days'
