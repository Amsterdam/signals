# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer

from signals.apps.signals import workflow
from signals.apps.signals.models import Status


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

        if obj.state in [workflow.HEROPEND, workflow.REACTIE_GEVRAAGD, workflow.REACTIE_ONTVANGEN, ]:
            return obj.state.upper()
        elif obj.state in [workflow.AFGEHANDELD, workflow.GEANNULEERD, workflow.GESPLITST, ]:
            return 'CLOSED'
        else:
            return 'OPEN'

    def get_public_state_display(self, obj):
        _status_state_translations = {workflow.HEROPEND: 'Heropend',
                                      workflow.GEANNULEERD: 'Afgesloten',
                                      workflow.AFGEHANDELD: 'Afgesloten',
                                      workflow.GESPLITST: 'Afgesloten',
                                      workflow.REACTIE_GEVRAAGD: 'Vraag aan u verstuurd',
                                      workflow.REACTIE_ONTVANGEN: 'Antwoord van u ontvangen'}
        return _status_state_translations.get(obj.state, 'Open')
