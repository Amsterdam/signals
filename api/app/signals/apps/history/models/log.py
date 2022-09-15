# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam
import uuid

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from signals.apps.feedback.models import _get_description_of_receive_feedback
from signals.apps.signals.models.history import EMPTY_HANDLING_MESSAGE_PLACEHOLDER_MESSAGE
from signals.apps.signals.models.location import _get_description_of_update_location
from signals.apps.signals.models.signal_departments import SignalDepartments
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
    data = models.JSONField(null=True)

    created_by = models.EmailField(null=True, blank=True)
    created_at = models.DateTimeField(editable=False)

    # This is a reference to a specific Signal. It can be blank if the object does not have a relation to a Signal.
    #
    # We want this to be here so that for the Signal history endpoint we can easily select all history for that specific
    # Signal.
    #
    # When creating history log for any changes on a Signal make sure to use the SignalLogService. In the future more
    # LogService classes can and will be created to facilitate the history logging of other objects.
    _signal = models.ForeignKey('signals.Signal', on_delete=models.CASCADE, related_name='history_log',
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

    def translate_content_type(self, content_type_name):
        """
        Present for backwards compatibility
        """
        content_type_translations = {
            'category assignment': 'category_assignment',
            'service level objective': 'sla',
            'type': 'type_assignment',
            'signal user': 'user_assignment',
        }

        if content_type_name in content_type_translations:
            return content_type_translations[content_type_name]
        elif content_type_name == 'signal departments':
            if self.object.relation_type == SignalDepartments.REL_ROUTING:
                content_type_name = 'routing_assignment'
            elif self.object.relation_type == SignalDepartments.REL_DIRECTING:
                content_type_name = 'directing_departments_assignment'
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
        # Note: this should produce a content_type.model not .name
        translations = {
            'category_assignment': 'categoryassignment',
            'sla': 'servicelevelobjective',
            'type_assignment': 'type',
            'user_assignment': 'signaluser',
            'routing_assignment': 'signaldepartments',
            'directing_departments_assignment': 'signaldepartments',
        }

        content_type = what[what.find('_') + 1:].lower()
        if content_type in translations:
            content_type = translations[content_type]
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
        what = self.what
        if what == 'UPDATE_STATUS':
            action = f'Status gewijzigd naar: {dict(STATUS_CHOICES).get(self.extra, "Onbekend")}'
        elif what == 'UPDATE_PRIORITY':
            translated = {'high': 'Hoog', 'normal': 'Normaal', 'low': 'Laag'}.get(self.extra, 'Onbekend')
            action = f'Urgentie gewijzigd naar: {translated}'
        elif what == 'UPDATE_CATEGORY_ASSIGNMENT':
            action = f'Categorie gewijzigd naar: {self.extra}'
        elif what == 'UPDATE_LOCATION':
            action = 'Locatie gewijzigd naar:'
        elif what == 'CREATE_NOTE':
            action = 'Notitie toegevoegd:'
        elif what == 'RECEIVE_FEEDBACK' or what == 'CREATE_FEEDBACK':
            action = 'Feedback van melder ontvangen'
        elif what == 'UPDATE_TYPE_ASSIGNMENT':
            action = f'Type gewijzigd naar: {_history_translated_action(self.extra)}'
        elif what == 'UPDATE_DIRECTING_DEPARTMENTS_ASSIGNMENT':
            action = f'Regie gewijzigd naar: {self.extra or "Verantwoordelijke afdeling"}'
        elif what == 'UPDATE_ROUTING_ASSIGNMENT':
            action = f'Routering: afdeling/afdelingen gewijzigd naar: {self.extra or "Verantwoordelijke afdeling (routering)"}'  # noqa
        elif what == 'UPDATE_USER_ASSIGNMENT':
            if self.extra:
                action = f'Melding toewijzing gewijzigd naar: {self.extra}'
            else:
                action = 'Melding niet meer toegewezen aan behandelaar.'
        elif what == 'CREATE_SIGNAL' and self.object_pk != self._signal_id:
            action = 'Deelmelding toegevoegd'
        elif what == 'UPDATE_SLA':
            action = 'Servicebelofte:'
        else:
            action = 'Actie onbekend.'
        return action

    def get_description(self):
        """
        "get_description" copied from History
        Present for backwards compatibility
        """
        what = self.what
        if what == 'UPDATE_LOCATION':
            description = _get_description_of_update_location(int(self.object_pk))
        elif what == 'RECEIVE_FEEDBACK':
            description = _get_description_of_receive_feedback(uuid.UUID(self.object_pk))
        elif what == 'CHILD_SIGNAL_CREATED':
            description = f'Melding {self.extra}'
        elif what == 'UPDATE_SLA' and self.description is None:
            description = EMPTY_HANDLING_MESSAGE_PLACEHOLDER_MESSAGE
        else:
            description = self.description
        return description

    # END - Backwards compatibility functions
