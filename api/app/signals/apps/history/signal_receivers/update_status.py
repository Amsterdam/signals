# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.dispatch import receiver

from signals.apps.history.services import SignalLogService
from signals.apps.signals.managers import update_status


@receiver(update_status, dispatch_uid='update_status_log_handler')
def update_status_handler(sender, signal_obj, status, *args, **kwargs):
    """
    Create a log rule
    """
    SignalLogService.log_update_status(status)
