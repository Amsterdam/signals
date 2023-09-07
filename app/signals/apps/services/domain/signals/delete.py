# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
import logging
import uuid
from typing import Final

from django.conf import settings
from django.core.files.storage import default_storage
from django.db import transaction
from django.utils import timezone

from signals.apps.signals.models import DeletedSignal, Signal
from signals.apps.signals.workflow import AFGEHANDELD, GEANNULEERD, GESPLITST
from signals.celery import app

log = logging.getLogger(__name__)


class DeleteSignalsService:
    """
    A service class for deleting signals in a specific state after a certain period of time.

    This class provides methods for deleting signals that meet the specified criteria.
    """
    VALID_STATES: Final[list[str]] = [AFGEHANDELD, GEANNULEERD, GESPLITST, ]

    @staticmethod
    def run(state: str, days: int, delay_deletion: bool = False) -> uuid.UUID:
        """
        Run the deletion process for signals.

        Args:
            state (str): The state of signals to be deleted.
            days (int): The minimum number of days a signal should have been in the state to be eligible for deletion.
            delay_deletion (bool, optional): If True, delay the actual deletion process using celery.

        Raises:
            ValueError: If the provided state, days, or feature flag is invalid.
        """
        if not settings.FEATURE_FLAGS.get('DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED', False):
            raise ValueError('Feature flag "DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED" is not enabled')

        if state not in DeleteSignalsService.VALID_STATES:
            raise ValueError('Invalid state(s) provided must be one of '
                             f'"{", ".join(DeleteSignalsService.VALID_STATES)}"')

        if days < 365:
            raise ValueError('Invalid days provided must be at least 365')

        batch_uuid = uuid.uuid4()

        signal_qs = Signal.objects.filter(
            parent_id__isnull=True,
            status__state=state,
            status__created_at__lt=timezone.now() - timezone.timedelta(days=days)
        )

        for signal in signal_qs:
            if delay_deletion:
                DeleteSignalsService.delete_signal.delay(signal.id, batch_uuid)
            else:
                DeleteSignalsService.delete_signal(signal.id, batch_uuid)

        return batch_uuid

    @staticmethod
    @app.task(prio=0)
    def delete_signal(signal_id: int, batch_uuid: uuid.UUID = None):  # noqa C901
        """
        Delete a signal and associated data.

        Args:
            signal_id (int): The id of the signal to be deleted.
            batch_uuid (UUID, optional): A unique identifier for the deletion batch.
        """
        try:
            signal = Signal.objects.get(id=signal_id)
        except Signal.DoesNotExist:
            log.warning(f'Deleting Signal with id #{signal_id} went wrong, Signal no longer exists')
            return

        if signal.is_child:
            note = (f'Parent signal was in state "{signal.parent.status.get_state_display()}" '
                    f'for {(timezone.now() - signal.parent.status.created_at).days} days')
        else:
            note = (f'Signal was in state "{signal.status.get_state_display()}" '
                    f'for {(timezone.now() - signal.status.created_at).days} days')

        if signal.is_parent:
            # Delete children before deleting the parent
            for child_signal in signal.children.all():
                DeleteSignalsService.delete_signal(child_signal.id, batch_uuid)

        try:
            with transaction.atomic():
                DeletedSignal.objects.create_from_signal(signal=signal, action='automatic', note=note,
                                                         batch_uuid=batch_uuid)

                attachment_files = [attachment.file.path for attachment in signal.attachments.all()]
                signal.attachments.all().delete()

                signal.delete()

                for attachment_file in attachment_files:
                    if default_storage.exists(attachment_file):
                        default_storage.delete(attachment_file)
        except Exception as e:
            log.error(f'Deleting Signal with id #{signal.id} went wrong, error: {e}')
