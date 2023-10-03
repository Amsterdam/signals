# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2022 Gemeente Amsterdam
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from signals.apps.signals import workflow
from signals.apps.signals.models.mixins import CreatedUpdatedModel


class StatusMessageTemplate(CreatedUpdatedModel):
    """
    Standaard afmeld tekst

    Voor een categorie in een status zijn er X afmeld teksten
    """

    category = models.ForeignKey(to='Category', related_name='status_message_templates',
                                 on_delete=models.DO_NOTHING)
    state = models.CharField(max_length=20, choices=workflow.STATUS_CHOICES)

    title = models.CharField(max_length=255, blank=True, null=True)
    text = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0, db_index=True)

    is_active = models.BooleanField(default=False)  # SIG-4379 Status message templates should have an is_active flag

    class Meta:
        permissions = (
            ('sia_statusmessagetemplate_write', 'Wijzingen van standaardteksten'),  # SIG-2192
        )
        indexes = [
            models.Index(
                fields=[
                    'category',
                    'state',
                    'order',
                ]
            )
        ]
        ordering = (
            'category',
            'state',
            'order',
        )
        verbose_name = 'Standaard afmeldtekst'
        verbose_name_plural = 'Standaard afmeldteksten'

    def save(self, *args, **kwargs):
        # The default qs we need to perform our checks
        self.full_clean()
        qs = StatusMessageTemplate.objects.filter(category_id=self.category_id, state=self.state)

        if self.pk is None and qs.count() >= settings.STATUS_MESSAGE_TEMPLATE_MAX_INSTANCES:
            msg = f'Only {settings.STATUS_MESSAGE_TEMPLATE_MAX_INSTANCES} StatusMessageTemplate instances allowed ' \
                  'per Category/State combination'
            raise ValidationError(msg)

        # Save the instance
        super().save(*args, **kwargs)
