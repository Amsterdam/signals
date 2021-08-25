# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.dispatch import receiver

from signals.apps.history.services import SignalLogService
from signals.apps.signals.managers import create_note


@receiver(create_note, dispatch_uid='create_note_log_handler')
def create_note_handler(sender, signal_obj, note, *args, **kwargs):
    """
    Create a log rule
    """
    SignalLogService.log_create_note(note)
