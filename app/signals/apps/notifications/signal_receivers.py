# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2025 Delta10 B.V.
import logging

from django.dispatch import receiver

from signals.apps.signals.managers import update_status

from . import tasks
from ..signals.models import Signal, Status
from ... import settings

logger = logging.getLogger(__name__)

@receiver(update_status, dispatch_uid='update_status_send_notification')
def send_notification_for_updated_signal_status(sender, signal_obj: Signal, status: Status, *args, **kwargs):
    if not settings.SIGNALEN_APP_BACKEND_URL:
        return

    municipality_code = settings.MUNICIPALITY_CODE

    if not municipality_code:
        logger.warning("There is no MUNICIPALITY_CODE environment variable in the environment configured")
        return

    tasks.send_notification.delay(
        municipality_code=municipality_code,
        payload={
            'status_code': status.state,
            'signal_uuid': signal_obj.uuid,
            'signal_id': signal_obj.pk,
        },
        notification_type='UPDATE_STATUS'
    )