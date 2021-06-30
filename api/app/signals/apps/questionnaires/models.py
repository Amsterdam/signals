# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import uuid
from datetime import timedelta

from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

from signals.apps.questionnaires.fieldtypes import field_type_choices, get_field_type_class
from signals.apps.questionnaires.managers import (
    QuestionManager,
    QuestionnaireManager,
    SessionManager
)

SESSION_DURATION = 2 * 60 * 60  # Two hours default


class Question(models.Model):
    key = models.CharField(unique=True, max_length=255, null=True, blank=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(editable=False, auto_now_add=True)

    label = models.CharField(max_length=255)
    short_label = models.CharField(max_length=255)
    field_type = models.CharField(choices=field_type_choices(), max_length=255)
    next_rules = models.JSONField(null=True, blank=True)
    required = models.BooleanField(default=False)

    root = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='+')

    objects = QuestionManager()

    def __str__(self):
        return f'{self.key or self.uuid} ({self.field_type})'

    def _clean_next_rules(self, value):
        field_type_class = get_field_type_class(self)
        if field_type_class is None:
            raise ValidationError('field_type')
        return field_type_class().clean(value)

    def clean(self):
        if self.next_rules:
            self.next_rules = self._clean_next_rules(self.next_rules)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def ref(self):
        return self.key if self.key else self.uuid


class Questionnaire(models.Model):
    EXTRA_PROPERTIES = 'EXTRA_PROPERTIES'
    REACTION_REQUEST = 'REACTION_REQUEST'
    FEEDBACK_REQUEST = 'FEEDBACK_REQUEST'
    FLOW_CHOICES = (
        (EXTRA_PROPERTIES, 'Uitvraag'),
        (REACTION_REQUEST, 'Reactie gevraagd'),
        (FEEDBACK_REQUEST, 'Klanttevredenheidsonderzoek'),
    )

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(editable=False, auto_now_add=True)

    first_question = models.ForeignKey('Question', on_delete=models.CASCADE, null=True, related_name='+')
    flow = models.CharField(max_length=255, choices=FLOW_CHOICES, default=EXTRA_PROPERTIES)

    name = models.CharField(max_length=255, help_text='The name of the Questionnaire')
    description = models.TextField(blank=True, null=True, help_text='Describe the Questionnaire')
    is_active = models.BooleanField(default=True)

    objects = QuestionnaireManager()

    def __str__(self):
        return f'Questionnaire "{self.name or self.uuid}" ({"" if self.is_active else "not"} active)'


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
