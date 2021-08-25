# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import uuid

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from signals.apps.feedback.models import _get_description_of_receive_feedback
from signals.apps.signals.models.history import EMPTY_HANDLING_MESSAGE_PLACEHOLDER_MESSAGE
from signals.apps.signals.models.location import _get_description_of_update_location
from signals.apps.signals.models.type import _history_translated_action
from signals.apps.signals.workflow import STATUS_CHOICES


class Log(models.Model):
    ACTION_UNKNOWN = 'UNKNOWN'
    ACTION_CREATE = 'CREATE'
    ACTION_UPDATE = 'UPDATE'
    ACTION_DELETE = 'DELETE'
    ACTION_RECEIVE = 'RECEIVE'

    ACTION_CHOICES = (
        (ACTION_UNKNOWN, 'Unknown'),
        (ACTION_CREATE, 'Created'),
        (ACTION_UPDATE, 'Updated'),
        (ACTION_DELETE, 'Deleted'),
        (ACTION_RECEIVE, 'Received'),
    )

    content_type = models.ForeignKey(ContentType, on_delete=models.DO_NOTHING, related_name='+')
    object_pk = models.CharField(max_length=128, db_index=True)
    object = GenericForeignKey('content_type', 'object_pk')

    action = models.CharField(editable=False, max_length=16, choices=ACTION_CHOICES, default=ACTION_UNKNOWN)
    description = models.TextField(max_length=3000, null=True, blank=True)
    extra = models.TextField(max_length=255, null=True, blank=True)

    created_by = models.EmailField(null=True, blank=True)
    created_at = models.DateTimeField(editable=False, auto_now_add=True)

    _signal = models.ForeignKey('signals.Signal', on_delete=models.DO_NOTHING, related_name='history_log',
                                blank=True, null=True)

    class Meta:
        ordering = ('-created_at',)
        index_together = (('content_type', 'object_pk',),)

    def __str__(self):
        representation = f'{self.action} on {self.content_type.name} #{self.object_pk}'
        if self._signal:
            representation = f'{representation}, on signal #{self._signal_id}'
        return representation

    # START - Backwards compatibility functions
    #
    # To keep the history endpoint intact the following functions are defined to mimic the history view in the database

    @staticmethod
    def translate_content_type(content_type_name):
        """
        Present for backwards compatibility
        """
        content_type_translations = {'category assignment': 'category_assignment',
                                     'service level objective': 'sla',
                                     'type': 'type_assignment'}
        if content_type_name in content_type_translations:
            return content_type_translations[content_type_name]
        return content_type_name

    @staticmethod
    def translate_what_to_action(what):
        """
        Present for backwards compatibility
        """
        return what[:what.find('_')]

    @staticmethod
    def translate_what_to_content_type(what):
        """
        Present for backwards compatibility
        """
        content_type = what[what.find('_') + 1:].lower()
        t = {'category_assignment': 'categoryassignment', 'sla': 'servicelevelobjective', 'type_assignment': 'type'}
        if content_type in t:
            content_type = t[content_type]
        return content_type

    @property
    def identifier(self):
        """
        "identifier" in the style of the signals_history_view
        Present for backwards compatibility
        """
        return f'{self.what}_{self.object_pk}'

    @property
    def what(self):
        """
        "what" in the style of the signals_history_view
        Present for backwards compatibility
        """
        translated_content_type = self.translate_content_type(self.content_type.name)
        return f'{self.action}_{translated_content_type}'.upper()

    @property
    def who(self):
        """
        "who" in the style of the signals_history_view
        Present for backwards compatibility
        """
        return self.created_by or 'Signalen systeem'

    def get_action(self):  # noqa C901
        """
        "get_action" copied from History
        Present for backwards compatibility
        """
        if self.what == 'UPDATE_STATUS':
            action = f'Status gewijzigd naar: {dict(STATUS_CHOICES).get(self.extra, "Onbekend")}'
        elif self.what == 'UPDATE_PRIORITY':
            translated = {'high': 'Hoog', 'normal': 'Normaal', 'low': 'Laag'}.get(self.extra, 'Onbekend')
            action = f'Urgentie gewijzigd naar: {translated}'
        elif self.what == 'UPDATE_CATEGORY_ASSIGNMENT':
            action = f'Categorie gewijzigd naar: {self.extra}'
        elif self.what == 'UPDATE_LOCATION':
            action = 'Locatie gewijzigd naar:'
        elif self.what == 'CREATE_NOTE':
            action = 'Notitie toegevoegd:'
        elif self.what == 'RECEIVE_FEEDBACK':
            action = 'Feedback van melder ontvangen'
        elif self.what == 'UPDATE_TYPE_ASSIGNMENT':
            action = f'Type gewijzigd naar: {_history_translated_action(self.extra)}'
        elif self.what == 'UPDATE_DIRECTING_DEPARTMENTS_ASSIGNMENT':
            action = f'Regie gewijzigd naar: {self.extra or "Verantwoordelijke afdeling"}'
        elif self.what == 'UPDATE_ROUTING_ASSIGNMENT':
            action = f'Routering: afdeling/afdelingen gewijzigd naar: {self.extra or "Verantwoordelijke afdeling (routering)"}'  # noqa
        elif self.what == 'UPDATE_USER_ASSIGNMENT':
            action = f'Melding toewijzing gewijzigd naar: {self.extra}'
        elif self.what == 'CHILD_SIGNAL_CREATED':
            action = 'Deelmelding toegevoegd'
        elif self.what == 'UPDATE_SLA':
            action = 'Servicebelofte:'
        else:
            action = 'Actie onbekend.'
        return action

    def get_description(self):
        """
        "get_description" copied from History
        Present for backwards compatibility
        """
        if self.what == 'UPDATE_LOCATION':
            description = _get_description_of_update_location(int(self.object_pk))
        elif self.what == 'RECEIVE_FEEDBACK':
            description = _get_description_of_receive_feedback(uuid.UUID(self.object_pk))
        elif self.what == 'CHILD_SIGNAL_CREATED':
            description = f'Melding {self.extra}'
        elif self.what == 'UPDATE_SLA' and self.description is None:
            description = EMPTY_HANDLING_MESSAGE_PLACEHOLDER_MESSAGE
        else:
            description = self.description
        return description

    # END - Backwards compatibility functions
