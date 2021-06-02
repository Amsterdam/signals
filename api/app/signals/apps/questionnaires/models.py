# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from datetime import timedelta
import uuid

from django.contrib.gis.db import models
from django.core.exceptions import ValidationError

from signals.apps.questionnaires.fieldtypes import field_type_choices, get_field_type_class

SESSION_DURATION = 2 * 60 * 60  # Two hours default


class Question(models.Model):
    key = models.CharField(unique=True, max_length=255, null=True, blank=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(editable=False, auto_now_add=True)

    field_type = models.CharField(choices=field_type_choices(), max_length=255)
    payload = models.JSONField(null=True, blank=True)
    required = models.BooleanField(default=False)

    root = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='+')

    def _clean_payload(self, value):
        field_type_class = get_field_type_class(self)
        if field_type_class is None:
            raise ValidationError('field_type')
        return field_type_class().clean(value)

    def clean(self):
        if self.payload:
            self.payload = self._clean_payload(self.payload)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Questionnaire(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(editable=False, auto_now_add=True)

    first_question = models.ForeignKey(
        'Question', on_delete=models.CASCADE, null=True, related_name='+')


class Answer(models.Model):
    created_at = models.DateTimeField(editable=False, auto_now_add=True)

    session = models.ForeignKey('Session', on_delete=models.CASCADE, null=True, related_name='answers')
    question = models.ForeignKey('Question', on_delete=models.CASCADE, null=True, related_name='+')

    payload = models.JSONField(blank=True, null=True)


class Session(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(editable=False, auto_now_add=True)

    started_at = models.DateTimeField(blank=True, null=True)
    submit_before = models.DateTimeField(blank=True, null=True)
    duration = models.DurationField(default=timedelta(seconds=SESSION_DURATION))

    questionnaire = models.ForeignKey('Questionnaire', on_delete=models.CASCADE, related_name='+')
    frozen = models.BooleanField(default=False)
