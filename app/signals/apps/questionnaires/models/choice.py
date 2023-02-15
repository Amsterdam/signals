# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam
from django.contrib.gis.db import models

from signals.apps.questionnaires.fieldtypes import get_field_type_class


class Choice(models.Model):
    question = models.ForeignKey('Question', on_delete=models.CASCADE, related_name='choices')
    selected = models.BooleanField(default=False)
    payload = models.JSONField(blank=True, null=True)
    display = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.display

    class Meta:
        order_with_respect_to = 'question'

    def clean_payload(self):
        field_type_class = get_field_type_class(self.question)
        return field_type_class.validate_submission_payload(self.answer_payload)

    def get_display(self):
        return self.display if self.display else self.payload
