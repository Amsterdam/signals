# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
import warnings

from signals.apps.services.domain.signals.delete import DeleteSignalsService
from signals.apps.signals.workflow import AFGEHANDELD, GEANNULEERD, GESPLITST
from signals.celery import app


@app.task
def delete_signals_in_state_for_x_days(state: str, days: int):
    """
    Asynchronous task to delete signals in a specific state that have been in that state for at least the specified
    number of days.

    Args:
        state (str): The state of signals to be deleted.
        days (int): The minimum number of days a signal should have been in the state to be eligible for deletion.

    Notes:
        This function delegates the deletion process to the DeleteSignalsService class,
        which handles the actual deletion logic.
    """
    DeleteSignalsService.run(state=state, days=days, delay_deletion=True)


@app.task
def delete_closed_signals(days=365):
    """
    Delete Signals in one of the Signalen system's closed states
    """
    message = ("The 'delete_closed_signals' celery task is deprecated. Instead, "
               "please use 'delete_signals_in_state_for_x_days' to achieve the "
               "same functionality.")
    warnings.warn(message, DeprecationWarning, stacklevel=2)

    DeleteSignalsService.run(state=AFGEHANDELD, days=days, delay_deletion=True)
    DeleteSignalsService.run(state=GEANNULEERD, days=days, delay_deletion=True)
    DeleteSignalsService.run(state=GESPLITST, days=days, delay_deletion=True)
