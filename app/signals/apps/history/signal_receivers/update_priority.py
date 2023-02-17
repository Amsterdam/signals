# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.dispatch import receiver

from signals.apps.history.services import SignalLogService
from signals.apps.signals.managers import update_priority


@receiver(update_priority, dispatch_uid='update_priority_log_handler')
def update_priority_handler(sender, signal_obj, priority, *args, **kwargs):
    """
    Create a log rule
    """
    SignalLogService.log_update_priority(priority)
