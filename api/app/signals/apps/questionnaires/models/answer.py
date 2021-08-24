# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.contrib.gis.db import models


class Answer(models.Model):
    """
    Answer to individual question in questionnaire.
    """
    created_at = models.DateTimeField(editable=False, auto_now_add=True)

    session = models.ForeignKey('Session', on_delete=models.CASCADE, null=True, related_name='answers')
    question = models.ForeignKey('Question', on_delete=models.CASCADE, null=True, related_name='+')

    payload = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f'Answer (id={self.id}) to question with analysis_key={self.question.analysis_key}.'
