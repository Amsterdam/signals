# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2023 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam, Delta10 B.V.
import typing

from django.contrib.gis.db import models

from signals.apps.signals.models.mixins import CreatedUpdatedModel


class EmailTemplate(CreatedUpdatedModel):
    SIGNAL_CREATED: typing.Final[str] = 'signal_created'
    SIGNAL_STATUS_CHANGED_AFGEHANDELD: typing.Final[str] = 'signal_status_changed_afgehandeld'
    SIGNAL_STATUS_CHANGED_INGEPLAND: typing.Final[str] = 'signal_status_changed_ingepland'
    SIGNAL_STATUS_CHANGED_HEROPEND: typing.Final[str] = 'signal_status_changed_heropend'
    SIGNAL_STATUS_CHANGED_OPTIONAL: typing.Final[str] = 'signal_status_changed_optional'
    SIGNAL_STATUS_CHANGED_REACTIE_GEVRAAGD: typing.Final[str] = 'signal_status_changed_reactie_gevraagd'
    SIGNAL_STATUS_CHANGED_REACTIE_ONTVANGEN: typing.Final[str] = 'signal_status_changed_reactie_ontvangen'
    SIGNAL_STATUS_CHANGED_AFGEHANDELD_KTO_NEGATIVE_CONTACT: typing.Final[str] =\
        'signal_status_changed_afgehandeld_kto_negative_contact'
    SIGNAL_STATUS_CHANGED_FORWARD_TO_EXTERNAL: typing.Final[str] = 'signal_forward_to_external'
    SIGNAL_FEEDBACK_RECEIVED: typing.Final[str] = 'signal_feedback_received'
    SIGNAL_FORWARD_TO_EXTERNAL_REACTION_RECEIVED: typing.Final[str] = 'signal_forward_to_external_reaction_received'
    MY_SIGNAL_TOKEN: typing.Final[str] = 'my_signal_token'
    SIGNAL_ASSIGNED: typing.Final[str] = 'signal_assigned'
    VERIFY_EMAIL_REPORTER: typing.Final[str] = 'verify_email_reporter'
    NOTIFY_CURRENT_REPORTER: typing.Final[str] = 'notify_current_reporter'

    KEYS_CHOICES: typing.Final = [
        (SIGNAL_CREATED, 'Send mail signal created'),
        (SIGNAL_STATUS_CHANGED_AFGEHANDELD, 'Send mail signal handled'),
        (SIGNAL_STATUS_CHANGED_INGEPLAND, 'Send mail signal scheduled'),
        (SIGNAL_STATUS_CHANGED_HEROPEND, 'Send mail signal reopened'),
        (SIGNAL_STATUS_CHANGED_OPTIONAL, 'Send mail optional'),
        (SIGNAL_STATUS_CHANGED_REACTIE_GEVRAAGD, 'Send mail signal reaction requested'),
        (SIGNAL_STATUS_CHANGED_REACTIE_ONTVANGEN, 'Send mail signal reaction requested received'),
        (SIGNAL_STATUS_CHANGED_AFGEHANDELD_KTO_NEGATIVE_CONTACT, 'Send mail signal negative KTO contact'),
        (SIGNAL_STATUS_CHANGED_FORWARD_TO_EXTERNAL, 'Send mail signal forwarded to external'),
        (SIGNAL_ASSIGNED, 'Send mail signal assigned'),
        (SIGNAL_FEEDBACK_RECEIVED, 'Send mail signal feedback received'),
        (SIGNAL_FORWARD_TO_EXTERNAL_REACTION_RECEIVED, 'Send mail forwarded to external reaction received'),
        (MY_SIGNAL_TOKEN, 'Send mail when a My Signals token has been requested'),
        (VERIFY_EMAIL_REPORTER, 'Send mail to verify the email address of a reporter'),
        (NOTIFY_CURRENT_REPORTER, 'Send mail to current reporter that a change of contact information is requested'),
    ]

    key = models.CharField(max_length=100, choices=KEYS_CHOICES, db_index=True, unique=True)
    title = models.CharField(max_length=255)
    body = models.TextField(help_text='Het is mogelijk om Markdown en template variabelen te gebruiken')
    created_by = models.EmailField(null=True, blank=True)

    class Meta:
        verbose_name = 'E-mail template'
        verbose_name_plural = 'E-mail templates'

    def __str__(self) -> str:
        return self.title
