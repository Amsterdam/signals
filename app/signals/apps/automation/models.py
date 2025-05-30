# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2025 Delta10 B.V.

from django.db import models
from signals.apps.signals.models import Expression
from signals.apps.signals import workflow


class ForwardToExternal(models.Model):
    """
    Automatically forward a created to an external e-mail
    """
    expression = models.OneToOneField(Expression, on_delete=models.CASCADE)
    email = models.EmailField()
    text = models.CharField(max_length=10000, null=True, blank=True)

    class Meta:
        verbose_name = 'Automatische externe doorstuurregel'
        verbose_name_plural = 'Automatische externe doorstuurregels'


class SetState(models.Model):
    """
    Automatically set a created signal to the state "Afgehandeld" or "Geannuleerd"
    """
    expression = models.OneToOneField(Expression, on_delete=models.CASCADE)
    desired_state = models.CharField(
        max_length=20,
        choices=(
            (workflow.AFGEHANDELD, 'Afgehandeld'),
            (workflow.GEANNULEERD, 'Geannuleerd'),
        ),
        help_text='Gewenste status'
    )
    text = models.CharField(max_length=10000, null=True, blank=True)

    class Meta:
        verbose_name = 'Automatische afhandelregel'
        verbose_name_plural = 'Automatische afhandelregels'