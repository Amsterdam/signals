# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.gis.db import models

from signals.apps.signals.models.mixins import CreatedUpdatedModel


class SignalDepartments(CreatedUpdatedModel):
    REL_DIRECTING = 'directing'
    REL_ROUTING = 'routing'
    REL_CHOICES = (
        (REL_DIRECTING, REL_DIRECTING),
        (REL_ROUTING, REL_ROUTING),
    )

    _signal = models.ForeignKey('signals.Signal', on_delete=models.CASCADE, related_name='signal_departments')
    departments = models.ManyToManyField('signals.Department', related_name='+')
    relation_type = models.CharField(max_length=20, choices=REL_CHOICES, default=REL_DIRECTING)
    created_by = models.EmailField(null=True, blank=True)

    history_log = GenericRelation('history.Log', object_id_field='object_pk')
