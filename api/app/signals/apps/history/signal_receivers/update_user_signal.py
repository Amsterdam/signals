# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.dispatch import receiver

from signals.apps.history.services import SignalLogService
from signals.apps.signals.managers import update_user_assignment


@receiver(update_user_assignment, dispatch_uid='update_user_assignment_log_handler')
def update_user_assignment_handler(sender, signal_obj, user_assignment, *args, **kwargs):
    """
    Create a log rule
    """
    SignalLogService.log_update_user_assignment(user_assignment)
