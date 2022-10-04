# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer

from signals.apps.signals.models import Status
from signals.apps.signals.workflow import AFGEHANDELD, GEANNULEERD, GESPLITST


class _NestedMySignalStatusSerializer(ModelSerializer):
    state = SerializerMethodField(method_name='get_public_state')
    state_display = SerializerMethodField(method_name='get_public_state_display')

    class Meta:
        model = Status
        fields = (
            'state',
            'state_display',
        )

    def get_public_state(self, obj):
        return 'CLOSED' if obj.state in [AFGEHANDELD, GEANNULEERD, GESPLITST, ] else 'OPEN'

    def get_public_state_display(self, obj):
        return 'Afgesloten' if obj.state in [AFGEHANDELD, GEANNULEERD, GESPLITST, ] else 'Open'
