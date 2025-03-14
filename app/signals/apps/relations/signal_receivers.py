# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2025 Delta10 B.V.
from django.core.exceptions import ValidationError
from django.dispatch import receiver

from signals.apps.signals.managers import (
    update_status,
)
from signals.apps.signals.models import Signal
from signals.apps.signals import workflow

from .models import Relation


@receiver((update_status), dispatch_uid='relations_update_status')
def update_status_handler(sender, signal_obj, status, prev_status, *args, **kwargs):
    if status.state == prev_status.state:
        return

    if status.state not in [workflow.AFGEHANDELD, workflow.GEANNULEERD, workflow.BEHANDELING, workflow.INGEPLAND, workflow.AFGEHANDELD]:
        return

    relations = Relation.objects.filter(source=signal_obj)

    for relation in relations:
        try:
            Signal.actions.update_status(data={
                'text': status.text,
                'state': status.state,
                'send_email': status.send_email
            }, signal=relation.target)
        except ValidationError:
            pass
