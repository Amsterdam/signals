from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from signals.apps.api.app_settings import (
    SIGNAL_API_STATE_OPEN,
    SIGNAL_API_STATE_OPEN_DISPLAY,
    SIGNALS_API_CLOSED_STATES,
    SIGNALS_API_STATE_CLOSED,
    SIGNALS_API_STATE_CLOSED_DISPLAY
)
from signals.apps.api.generics.serializers import SIAModelSerializer
from signals.apps.signals import workflow
from signals.apps.signals.models import Status


class _NestedStatusModelSerializer(SIAModelSerializer):
    state_display = serializers.CharField(source='get_state_display', read_only=True)

    class Meta:
        model = Status
        fields = (
            'text',
            'user',
            'state',
            'state_display',
            'target_api',
            'extra_properties',
            'created_at',
        )
        read_only_fields = (
            'created_at',
            'user',
        )

    def validate(self, attrs):
        if (attrs['state'] == workflow.TE_VERZENDEN
                and attrs.get('target_api') == Status.TARGET_API_SIGMAX):

            request = self.context.get('request')
            if request and not request.user.has_perm('signals.push_to_sigmax'):
                raise PermissionDenied({
                    'state': "You don't have permissions to push to Sigmax/CityControl."
                })

        return super(_NestedStatusModelSerializer, self).validate(attrs=attrs)


class _NestedPublicStatusModelSerializer(serializers.ModelSerializer):
    state_display = serializers.SerializerMethodField(method_name='get_public_state_display')
    state = serializers.SerializerMethodField(method_name='get_public_state')

    class Meta:
        model = Status
        fields = (
            'state',
            'state_display',
        )

    def get_public_state(self, obj):
        if obj.state in SIGNALS_API_CLOSED_STATES:
            return SIGNALS_API_STATE_CLOSED
        return SIGNAL_API_STATE_OPEN

    def get_public_state_display(self, obj):
        if obj.state in SIGNALS_API_CLOSED_STATES:
            return SIGNALS_API_STATE_CLOSED_DISPLAY
        return SIGNAL_API_STATE_OPEN_DISPLAY
