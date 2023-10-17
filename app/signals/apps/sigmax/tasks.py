# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2023 Gemeente Amsterdam
import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from signals.apps.sigmax.stuf_protocol.outgoing import handle
from signals.apps.signals import workflow
from signals.apps.signals.models import Signal, Status
from signals.celery import app

logger = logging.getLogger(__name__)


def _is_status_applicable(status: Status) -> bool:
    """
    Check if the given status is applicable for further processing in Sigmax.

    Parameters
    ----------
    status : Status
        The status object to be checked.

    Returns
    -------
    bool
        True if the status is applicable, False otherwise.

    Notes
    -----
    The status is considered applicable if the following conditions are met:
    - The state of the status is `workflow.TE_VERZENDEN`.
    - The target API of the status is `Status.TARGET_API_SIGMAX`.

    Examples
    --------
    >>> s = Status()
    >>> s.state = workflow.TE_VERZENDEN
    >>> s.target_api = Status.TARGET_API_SIGMAX
    >>> _is_status_applicable(s)
    True

    >>> s.state = workflow.TE_VERZENDEN
    >>> s.target_api = None
    >>> _is_status_applicable(s)
    False
    """
    return status.state == workflow.TE_VERZENDEN and status.target_api == Status.TARGET_API_SIGMAX


def is_signal_applicable(signal: Signal) -> bool:
    """
    Check if the given signal is applicable for further processing.

    Parameters
    ----------
    signal : Signal
        The signal object to be checked.

    Returns
    -------
    bool
        True if the signal is applicable, False otherwise.

    Notes
    -----
    The signal is considered applicable if the status of the signal is applicable based on
    the `_is_status_applicable` function.

    Examples
    --------
    >>> s = Signal()
    >>> s.status = Status()
    >>> s.status.state = workflow.TE_VERZENDEN
    >>> s.status.target_api = Status.TARGET_API_SIGMAX
    >>> is_signal_applicable(s)
    True

    >>> s.status.target_api = Status.TARGET_API_GISIB
    >>> is_signal_applicable(s)
    False
    """
    assert signal.status is not None

    return _is_status_applicable(signal.status)


@app.task
def push_to_sigmax(signal_id: int) -> None:
    """
    Push the signal with the given ID to Sigmax if applicable.

    Parameters
    ----------
    signal_id : int
        The ID of the signal to be pushed.

    Notes
    -----
    This function attempts to retrieve the signal with the given ID from the database.
    If the signal exists, it checks if the signal is applicable for further processing
    using the `is_signal_applicable` function. If applicable, the signal is handled
    by calling the `handle` function.

    If the signal with the given ID does not exist, an exception is logged.

    Examples
    --------
    >>> push_to_sigmax(123)
    # If signal with ID 123 exists and is applicable, it will be handled
    """
    try:
        signal = Signal.objects.get(pk=signal_id)
    except Signal.DoesNotExist as e:
        logger.exception(e)
    else:
        if is_signal_applicable(signal):
            handle(signal)


@app.task
def fail_stuck_sending_signals() -> None:
    """
    Fail signals that are stuck in the sending state for too long.

    Notes
    -----
    This function identifies signals that are in the sending state (`workflow.TE_VERZENDEN`)
    and have a target API of `Status.TARGET_API_SIGMAX`. It checks if the signals have been
    in the sending state for longer than the specified timeout period (`settings.SIGMAX_SEND_FAIL_TIMEOUT_MINUTES`).
    If such signals are found, their status is updated to `workflow.VERZENDEN_MISLUKT` and a failure message
    is added to the status text.

    Examples
    --------
    >>> fail_stuck_sending_signals()
    # If there are signals stuck in the sending state for too long, they will be marked as failed
    """
    before = timezone.now() - timedelta(minutes=float(settings.SIGMAX_SEND_FAIL_TIMEOUT_MINUTES))
    stuck_signals = Signal.objects.filter(status__state=workflow.TE_VERZENDEN,
                                          status__target_api=Status.TARGET_API_SIGMAX,
                                          status__updated_at__lte=before)

    for signal in stuck_signals:
        Signal.actions.update_status(data={
            'state': workflow.VERZENDEN_MISLUKT,
            'text': 'Melding stond langer dan {} minuten op TE_VERZENDEN. Mislukt'.format(
                settings.SIGMAX_SEND_FAIL_TIMEOUT_MINUTES
            )
        }, signal=signal)
