# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.gis.db import models

from signals.apps.signals.models.mixins import CreatedUpdatedModel


class Note(CreatedUpdatedModel):
    """Notes field for `Signal` instance."""
    _signal = models.ForeignKey('signals.Signal',
                                related_name='notes',
                                null=False,
                                on_delete=models.CASCADE)
    text = models.TextField(max_length=3000)
    created_by = models.EmailField(null=True, blank=True)  # analoog Priority model

    history_log = GenericRelation('history.Log', object_id_field='object_pk')

    class Meta:
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['created_at']),
        ]
