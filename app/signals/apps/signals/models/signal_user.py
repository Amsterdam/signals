# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.gis.db import models

from signals.apps.signals.models.mixins import CreatedUpdatedModel

User = get_user_model()


class SignalUser(CreatedUpdatedModel):
    """
    relation for assigning user to signal
    """

    _signal = models.ForeignKey('signals.Signal', on_delete=models.CASCADE, blank=True) # noqa
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, blank=True, null=True)
    created_by = models.EmailField(null=True, blank=True)

    history_log = GenericRelation('history.Log', object_id_field='object_pk')
