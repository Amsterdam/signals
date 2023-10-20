# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
import logging
import uuid
import warnings
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from signals.apps.signals.models import DeletedSignal, Signal
from signals.apps.signals.workflow import AFGEHANDELD, GEANNULEERD, GESPLITST
from signals.celery import app

log = logging.getLogger(__name__)


@app.task
def delete_signals_in_state_for_x_days(state: str, days: int):
    """
    Asynchronous task to delete signals in a specific state that have been in that state for at least the specified
    number of days.

    Args:
        state (str): The state of signals to be deleted.
        days (int): The minimum number of days a signal should have been in the state to be eligible for deletion.
    """
    if not settings.FEATURE_FLAGS.get('DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED', False):
        raise ValueError('Feature flag "DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED" is not enabled')

    if state not in [AFGEHANDELD, GEANNULEERD, GESPLITST, ]:
        raise ValueError('Invalid state(s) provided must be one of '
                         f'"{", ".join([AFGEHANDELD, GEANNULEERD, GESPLITST, ])}"')

    if days < 365:
        raise ValueError('Invalid days provided must be at least 365')

    batch_uuid = uuid.uuid4()

    signal_qs = Signal.objects.filter(
        parent_id__isnull=True,
        status__state=state,
        status__created_at__lt=timezone.now() - timedelta(days=days)
    )
    for signal in signal_qs:
        delete_signal.delay(signal.id, batch_uuid)


@app.task(prio=0)
def delete_signal(signal_id: int, batch_uuid: uuid.UUID | None = None):  # noqa C901
    """
    Delete a signal and associated data.

    Args:
        signal_id (int): The id of the signal to be deleted.
        batch_uuid (UUID, optional): A unique identifier for the deletion batch.
    """
    try:
        signal = Signal.objects.get(id=signal_id)
    except Signal.DoesNotExist:
        log.warning(f'Deleting Signal with id #{signal_id} went wrong, Signal does not exists')
        return

    if signal.is_parent:
        # Delete children before deleting the parent
        for child_signal in signal.children.all():
            delete_signal(child_signal.id, batch_uuid)

    if signal.is_child:
        assert signal.parent and signal.parent.status
        note = (f'Parent signal was in state "{signal.parent.status.get_state_display()}" '
                f'for {(timezone.now() - signal.parent.status.created_at).days} days')
    else:
        assert signal.status
        note = (f'Signal was in state "{signal.status.get_state_display()}" '
                f'for {(timezone.now() - signal.status.created_at).days} days')

    try:
        with transaction.atomic():
            DeletedSignal.objects.create_from_signal(signal=signal, action='automatic', note=note,
                                                     batch_uuid=batch_uuid)

            for attachment in signal.attachments.all():
                attachment.delete()

            signal.delete()
    except Exception as e:
        logging.error(f'Deleting Signal with id #{signal.id} went wrong, error: {e}')


@app.task
def delete_closed_signals(days: int = 365):
    """
    Delete Signals in one of the Signalen system's closed states
    """
    message = ("The 'delete_closed_signals' celery task is deprecated. Instead, "
               "please use 'delete_signals_in_state_for_x_days' to achieve the "
               "same functionality.")
    warnings.warn(message, DeprecationWarning, stacklevel=2)

    delete_signals_in_state_for_x_days.delay(state=AFGEHANDELD, days=days)
    delete_signals_in_state_for_x_days.delay(state=GEANNULEERD, days=days)
    delete_signals_in_state_for_x_days.delay(state=GESPLITST, days=days)
