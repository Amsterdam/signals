# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
from django.contrib.gis.db import models

from signals.apps.signals.models.mixins import CreatedUpdatedModel


class EmailTemplate(CreatedUpdatedModel):
    SIGNAL_CREATED = 'signal_created'
    SIGNAL_STATUS_CHANGED_AFGEHANDELD = 'signal_status_changed_afgehandeld'
    SIGNAL_STATUS_CHANGED_INGEPLAND = 'signal_status_changed_ingepland'
    SIGNAL_STATUS_CHANGED_HEROPEND = 'signal_status_changed_heropend'
    SIGNAL_STATUS_CHANGED_OPTIONAL = 'signal_status_changed_optional'
    SIGNAL_STATUS_CHANGED_REACTIE_GEVRAAGD = 'signal_status_changed_reactie_gevraagd'
    SIGNAL_STATUS_CHANGED_REACTIE_ONTVANGEN = 'signal_status_changed_reactie_ontvangen'
    Signal_STATUS_CHANGED_AFGEHANDELD_KTO_NEGATIVE_CONTACT = 'signal_status_changed_afgehandeld_kto_negative_contact'

    KEYS_CHOICES = [
        (SIGNAL_CREATED, 'Send mail signal created'),
        (SIGNAL_STATUS_CHANGED_AFGEHANDELD, 'Send mail signal handled'),
        (SIGNAL_STATUS_CHANGED_INGEPLAND, 'Send mail signal scheduled'),
        (SIGNAL_STATUS_CHANGED_HEROPEND, 'Send mail signal reopened'),
        (SIGNAL_STATUS_CHANGED_OPTIONAL, 'Send mail optional'),
        (SIGNAL_STATUS_CHANGED_REACTIE_GEVRAAGD, 'Send mail signal reaction requested'),
        (SIGNAL_STATUS_CHANGED_REACTIE_ONTVANGEN, 'Send mail signal reaction requested received'),
        (Signal_STATUS_CHANGED_AFGEHANDELD_KTO_NEGATIVE_CONTACT, 'Send mail signal '),
    ]

    key = models.CharField(max_length=100, choices=KEYS_CHOICES, db_index=True)
    title = models.CharField(max_length=255)
    body = models.TextField(help_text='Het is mogelijk om Markdown en template variabelen te gebruiken')
    created_by = models.EmailField(null=True, blank=True)

    class Meta:
        verbose_name = 'E-mail template'
        verbose_name_plural = 'E-mail templates'

    def __str__(self):
        return self.title
