# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.dispatch import receiver

from signals.apps.history.services import SignalLogService
from signals.apps.signals.managers import update_type


@receiver(update_type, dispatch_uid='update_type_log_handler')
def update_type_handler(sender, signal_obj, type, *args, **kwargs):
    """
    Create a log rule
    """
    SignalLogService.log_update_type(type)
