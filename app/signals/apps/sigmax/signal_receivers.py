# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2023 Gemeente Amsterdam
from django.dispatch import receiver

from signals.apps.sigmax import tasks
from signals.apps.sigmax.tasks import is_signal_applicable
from signals.apps.signals.managers import update_status


@receiver(update_status, dispatch_uid='sigmax_update_status')
def update_status_handler(sender, signal_obj, status, prev_status, **kwargs):
    """
    Update status handler for signals.

    Parameters
    ----------
    sender : Any
        The sender of the signal.
    signal_obj : Signal
        The signal object being updated.
    status : Status
        The new status of the signal.
    prev_status : Status
        The previous status of the signal.
    **kwargs : dict
        Additional keyword arguments.

    Notes
    -----
    This function is a signal receiver for the `update_status` signal. It is triggered
    whenever the status of a signal is updated. The function checks if the updated signal
    is applicable for further processing using the `is_signal_applicable` function.
    If applicable, it schedules the `push_to_sigmax` task to be executed asynchronously
    using the `delay` method.

    Examples
    --------
    This function is meant to be used as a signal receiver and is not called directly.
    When a signal's status is updated, this function will handle the update accordingly.
    """
    if is_signal_applicable(signal_obj):
        tasks.push_to_sigmax.delay(signal_id=signal_obj.id)
