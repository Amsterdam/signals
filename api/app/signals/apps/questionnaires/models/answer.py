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

    def extra_property(self):
        """
        Helper function for backwards compatibility with the "old" way how the extra_properties where populated.
        Will be removed when the FE has been migrated to only use the new Questionnaires app.
        """
        # Check if the field type of the question knows how to represent itself as an old extra property
        field_type = self.question.field_type_class()
        if extra_property_representation := field_type.extra_property(self):
            return extra_property_representation

        # Default
        return {
            'id': self.question.analysis_key,
            'label': self.question.short_label,
            'answer': self.payload,
        }
