# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.gis.db import models

from signals.apps.signals.models.mixins import CreatedUpdatedModel


class Priority(CreatedUpdatedModel):
    PRIORITY_LOW = 'low'
    PRIORITY_NORMAL = 'normal'
    PRIORITY_HIGH = 'high'
    PRIORITY_CHOICES = (
        (PRIORITY_LOW, 'Low'),
        (PRIORITY_NORMAL, 'Normal'),
        (PRIORITY_HIGH, 'High'),
    )

    _signal = models.ForeignKey('signals.Signal',
                                related_name='priorities',
                                null=False,
                                on_delete=models.CASCADE)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default=PRIORITY_NORMAL)
    created_by = models.EmailField(null=True, blank=True)

    history_log = GenericRelation('history.Log', object_id_field='object_pk')

    class Meta:
        verbose_name_plural = 'Priorities'

    def __str__(self):
        """String representation."""
        return self.get_priority_display()
