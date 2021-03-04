# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
from rest_framework import serializers

from signals.apps.api.generics.serializers import SIAModelSerializer
from signals.apps.signals.models import Type


class _NestedTypeModelSerializer(SIAModelSerializer):
    code = serializers.CharField(source='name', max_length=3)

    class Meta:
        model = Type
        fields = (
            'code',
            'created_at',
            'created_by'
        )
