# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.dispatch import receiver

from signals.apps.history.services import SignalLogService
from signals.apps.signals.managers import update_signal_departments


@receiver(update_signal_departments, dispatch_uid='update_signal_departments_log_handler')
def update_signal_departments_handler(sender, signal_obj, signal_departments, *args, **kwargs):
    """
    Create a log rule
    """
    SignalLogService.log_update_signal_departments(signal_departments)
