# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 -2022 Gemeente Amsterdam
from django.db.models.signals import post_save
from django.dispatch import receiver

from signals.apps.history.services import SignalLogService
from signals.apps.signals.models import Note


@receiver(post_save, sender=Note, dispatch_uid='create_note_log_handler')
def create_note_handler(sender, instance, *args, **kwargs):
    """
    Create a log rule
    """
    SignalLogService.log_create_note(instance)
