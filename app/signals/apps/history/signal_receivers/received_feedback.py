# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.db.models.signals import post_save
from django.dispatch import receiver

from signals.apps.feedback.models import Feedback
from signals.apps.history.services import SignalLogService


@receiver(post_save, sender=Feedback, dispatch_uid='receive_feedback_log_handler')
def receive_feedback_handler(sender, instance, created, *args, **kwargs):
    """
    Create a log rule
    """
    if not created:
        SignalLogService.log_receive_feedback(instance)
