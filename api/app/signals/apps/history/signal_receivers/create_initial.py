# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.dispatch import receiver

from signals.apps.history.services import SignalLogService
from signals.apps.signals.managers import create_initial


@receiver(create_initial, dispatch_uid='create_initial_log_handler')
def create_initial_handler(sender, signal_obj, *args, **kwargs):
    """
    Create all log rules needed for the "create initial" action
    """
    SignalLogService.log_create_initial(signal_obj)
