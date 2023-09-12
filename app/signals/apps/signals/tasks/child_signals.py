# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from signals.apps.services.domain.auto_create_children.service import AutoCreateChildrenService
from signals.apps.signals.models.signal import Signal
from signals.apps.signals.workflow import AFGEHANDELD, GEANNULEERD
from signals.celery import app


@app.task
def update_status_children_based_on_parent(signal_id):
    signal = Signal.objects.get(pk=signal_id)
    if signal.is_parent and signal.status.state in [AFGEHANDELD, GEANNULEERD, ]:
        text = 'Hoofdmelding is afgehandeld'

        # Lets check the children
        children = signal.children.exclude(status__state__in=[AFGEHANDELD, GEANNULEERD, ])
        for child in children:
            # All children must get the state "GEANNULEERD"
            data = dict(state=GEANNULEERD, text=text)
            Signal.actions.update_status(data=data, signal=child)


@app.task
def apply_auto_create_children(signal_id):
    """
    !!! This will be refactored when the "uitvraag" will be moved to the API !!!

    :param signal_id:
    """
    AutoCreateChildrenService.run(signal_id=signal_id)
