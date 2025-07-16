# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2025 Delta10 B.V.

from django.db import models
from signals.apps.signals.models import Expression


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