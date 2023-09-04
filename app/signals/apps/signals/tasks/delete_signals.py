# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from signals.apps.services.domain.delete_signals import SignalDeletionService
from signals.apps.signals.workflow import AFGEHANDELD, GEANNULEERD, GESPLITST
from signals.celery import app


@app.task
def delete_closed_signals(days=365):
    """
    Delete Signals in one of the Signalen system's closed states
    """
    SignalDeletionService().delete_signals(AFGEHANDELD, days, dry_run=False)
    SignalDeletionService().delete_signals(GEANNULEERD, days, dry_run=False)
    SignalDeletionService().delete_signals(GESPLITST, days, dry_run=False)
