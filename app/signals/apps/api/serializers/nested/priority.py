# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from signals.apps.api.generics.serializers import SIAModelSerializer
from signals.apps.signals.models import Priority


class _NestedPriorityModelSerializer(SIAModelSerializer):
    class Meta:
        model = Priority
        fields = (
            'priority',
            'created_by',
        )
        read_only_fields = (
            'created_by',
        )
