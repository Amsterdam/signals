# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Delta10 B.V.
from django.db import models

from signals.apps.signals.models import Signal


class Case(models.Model):
    """Relate a Signal to a case in an external system"""
    _signal = models.OneToOneField(
        Signal,
        related_name='zgw_case',
        on_delete=models.CASCADE,
    )

    external_id = models.CharField(max_length=100, db_index=True)

    def __str__(self):
        return str(self._signal.id)
