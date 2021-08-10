# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import uuid
from datetime import timedelta

from django.contrib.gis.db import models
from django.utils import timezone

from signals.apps.questionnaires.app_settings import SESSION_DURATION
from signals.apps.questionnaires.managers import SessionManager


class Session(models.Model):
    """
    Sessions keep track of incoming answers and store them after questionnaire
    is finished.
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(editable=False, auto_now_add=True)

    started_at = models.DateTimeField(blank=True, null=True)
    submit_before = models.DateTimeField(blank=True, null=True)
    duration = models.DurationField(default=timedelta(seconds=SESSION_DURATION))

    questionnaire = models.ForeignKey('Questionnaire', on_delete=models.CASCADE, related_name='+')
    frozen = models.BooleanField(default=False)
    _signal = models.ForeignKey('signals.Signal', on_delete=models.CASCADE, null=True)

    objects = SessionManager()

    @property
    def is_expired(self):
        return (
            (self.submit_before and self.submit_before < timezone.now()) or
            (self.started_at and self.started_at + self.duration < timezone.now())
        )

    @property
    def too_late(self):
        return not self.frozen or self.is_expired
