# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 -2022 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
import uuid

from django.contrib.gis.db import models

from signals.apps.questionnaires.fieldtypes import field_type_choices, get_field_type_class
from signals.apps.questionnaires.managers import QuestionManager


class Question(models.Model):
    """
    Question to be included in one or more Questionnaires.

    Questions are not directly inserted into a Questionnaire, instead Questions
    are added to a graph that is referred to by a Questionnaire. A question may
    appear in several graphs and hence Questionnaires. See the QuestionGraph and
    Edge models as to how the questions are referred to.
    """
    retrieval_key = models.CharField(unique=True, max_length=255, null=True, blank=True)
    analysis_key = models.CharField(max_length=255, default='PLACEHOLDER')
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(editable=False, auto_now_add=True)

    label = models.CharField(max_length=1000)  # noqa SIG-4511 raised the max length. The ticket states a max length of 400, but to be future proof raised to 1000
    short_label = models.CharField(max_length=255)
    field_type = models.CharField(choices=field_type_choices(), max_length=255)
    required = models.BooleanField(default=False)
    enforce_choices = models.BooleanField(default=False)

    multiple_answers_allowed = models.BooleanField(default=False)
    multiple_answer_schema = {
        'type': 'object',
        'properties': {
            'answers': {
                'type': 'object',
                'properties': {
                    'minItems': {
                        'type': 'integer',
                        'minimum': 1,
                        'maximum': 100,
                    },
                    'maxItems': {
                        'type': 'integer',
                        'minimum': 1,
                        'maximum': 100,
                    },
                },
                'required': [
                    'minItems',
                    'maxItems',
                ],
            },
        },
        'required': [
            'answers',
        ],
    }

    # JSON schema for additional validation of the payload of a given answer/answers
    # For example the minItems and the maxItems when given multiple ansers
    additional_validation = models.JSONField(null=True, blank=True)

    # Extra properties needed for the question
    # For example the field_type selected_object has a property that stores the source URL of the objects
    extra_properties = models.JSONField(blank=True, null=True)

    objects = QuestionManager()

    def __str__(self):
        return f'{self.retrieval_key or self.uuid} ({self.field_type})'

    @property
    def ref(self):
        return self.retrieval_key if self.retrieval_key else str(self.uuid)

    def save(self, *args, **kwargs):
        if self.analysis_key == 'PLACEHOLDER':
            self.analysis_key = f'PLACEHOLDER-{str(self.uuid)}'

        return super().save(*args, **kwargs)

    @property
    def field_type_class(self):
        return get_field_type_class(self)

    def get_field_type(self):
        kwargs = {}
        if self.multiple_answers_allowed and self.additional_validation and 'answers' in self.additional_validation:
            min_items = self.additional_validation['answers']['minItems']
            max_items = self.additional_validation['answers']['maxItems']
            kwargs.update({'multiple_answers_allowed': self.multiple_answers_allowed, 'min_items': min_items,
                           'max_items': max_items})
        elif self.multiple_answers_allowed:
            kwargs.update({'multiple_answers_allowed': self.multiple_answers_allowed, 'min_items': 1, 'max_items': 10})

        return self.field_type_class(**kwargs)
