# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.dispatch import receiver

from signals.apps.history.services import SignalLogService
from signals.apps.signals.managers import update_category_assignment


@receiver(update_category_assignment, dispatch_uid='update_category_assignment_log_handler')
def update_category_assignment_handler(sender, signal_obj, category_assignment, *args, **kwargs):
    """
    Create a log rule
    """
    SignalLogService.log_update_category_assignment(category_assignment)
