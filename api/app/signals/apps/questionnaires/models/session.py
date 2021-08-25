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
    duration = models.DurationField(default=timedelta(seconds=SESSION_DURATION), blank=True, null=True)

    questionnaire = models.ForeignKey('Questionnaire', on_delete=models.CASCADE, related_name='+')
    frozen = models.BooleanField(default=False)
    _signal = models.ForeignKey('signals.Signal', on_delete=models.CASCADE, null=True)

    objects = SessionManager()

    @property
    def is_expired(self):
        """
        Check overall deadline and maximum duration for filling out for expiry.

        Both overall deadline, called `submit_before`, and maximum duration that
        can be taken to fill out a questionnaire are considered (either or both)
        can take a None value. The submission deadline is not extended with
        the value of duration. So if you are allowed two hours to fill out the
        questionnaire, but start it 5 minutes before the submission deadline
        you will effectively only have 5 minutes to fill it out and submit it.

        If you want no deadline, set `submit_before` to None and set `duration`
        to None. If you only want to enforce the time taken to fill out the
        questionnaire set `submit_before` to None and `duration` to the
        desired duration.
        """
        return (
            (self.submit_before and self.submit_before < timezone.now()) or
            (self.started_at and self.duration and self.started_at + self.duration < timezone.now())
        )

    @property
    def too_late(self):
        return not self.frozen or self.is_expired
