# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
import uuid

from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.gis.db import models

from signals.apps.questionnaires.managers import QuestionnaireManager
from signals.apps.questionnaires.models.attached_section import AttachedSection


class Questionnaire(models.Model):
    """
    Questionnaire used in one of three flows for Signalen.

    - Reaction requests: Ask a reporter/complainant for extra information or
      photos that might be needed to resolve the Signal/complaint.
    - Feedback requests: Ask a reporter/complainant whether Signal/complaint
      resolution. Can lead to that Signal/complaint being re-opened.
    - Generic questionnaires: The extra_properties of a Signal/complaint are
      filled using generic questionnaires triggered per category.
    """
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
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True, help_text='Describe the Questionnaire')
    is_active = models.BooleanField(default=False)

    graph = models.ForeignKey(
        'QuestionGraph', on_delete=models.SET_NULL, related_name='questionnaire', null=True, blank=True)
    flow = models.CharField(max_length=255, choices=FLOW_CHOICES, default=EXTRA_PROPERTIES)

    # Attached section comprise of a title, a text and possibly zero or more
    # images. A questionnaire can have zero or more of these sections.
    attached_sections = GenericRelation(AttachedSection)

    objects = QuestionnaireManager()

    def __str__(self):
        return f'Questionnaire "{self.name or self.uuid}" ({"" if self.is_active else "not"} active)'

    @property
    def first_question(self):
        if self.graph:
            return self.graph.first_question
        return None
