# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.dispatch import receiver

from signals.apps.history.services import SignalLogService
from signals.apps.signals.managers import update_location


@receiver(update_location, dispatch_uid='update_location_log_handler')
def update_location_handler(sender, signal_obj, location, *args, **kwargs):
    """
    Create a log rule
    """
    SignalLogService.log_update_location(location)
