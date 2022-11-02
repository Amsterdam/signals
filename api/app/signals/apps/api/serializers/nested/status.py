# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2022 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import MaxLengthValidator
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError

from signals.apps.api.app_settings import (
    SIGNAL_API_STATE_OPEN,
    SIGNAL_API_STATE_OPEN_DISPLAY,
    SIGNALS_API_CLOSED_STATES,
    SIGNALS_API_STATE_CLOSED,
    SIGNALS_API_STATE_CLOSED_DISPLAY
)
from signals.apps.api.generics.serializers import SIAModelSerializer
from signals.apps.services.domain.permissions.signal import SignalPermissionService
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
            'send_email',
            'created_at',
            'email_override',
        )
        read_only_fields = (
            'created_at',
            'user',
        )

    def validate(self, attrs):
        """
        Validate data, specifically extra rules for `state` attribute.
        """
        self._validate_state_TE_VERZENDEN(attrs)
        self._validate_state_REACTIE_GEVRAAGD(attrs)
        self._validate_state_DOORZETTEN_NAAR_EXTERN(attrs)

        return super().validate(attrs=attrs)

    def _validate_state_TE_VERZENDEN(self, attrs):
        """
        Validate all info for TE_VERZENDEN flow is present.

        Note: This state is only used for communication with the CityControl
        system (by the Sigmax company).
        """
        if (attrs['state'] == workflow.TE_VERZENDEN
                and attrs.get('target_api') == Status.TARGET_API_SIGMAX):

            request = self.context.get('request')

            if request and not SignalPermissionService.has_permission(request.user, 'signals.push_to_sigmax'):
                raise PermissionDenied({
                    'state': "You don't have permissions to push to Sigmax/CityControl."
                })

    def _validate_state_REACTIE_GEVRAAGD(self, attrs):
        """
        Validate all info for REACTIE_GEVRAAGS flow is present.
        """
        if attrs['state'] == workflow.REACTIE_GEVRAAGD:  # SIG-3887
            signal = self.context['view'].get_object()
            if not signal.reporter.email:
                msg = 'No email address known for signal with ID={{ signal.id }}.'
                raise ValidationError({'state': msg})

            # SIG-4511
            # Check if the given text has a maximum length of 400 characters.
            # If not, raise a validation error.
            try:
                MaxLengthValidator(limit_value=400)(attrs['text'])
            except DjangoValidationError as e:
                raise ValidationError({'text': e.messages})

    def _validate_state_DOORZETTEN_NAAR_EXTERN(self, attrs):
        """
        Validate all info for DOORZETTEN_NAAR_EXTERN flow is present.
        """
        if attrs['state'] == workflow.DOORZETTEN_NAAR_EXTERN:  # ps-261
            if not (attrs['email_override'] and attrs['send_email'] and attrs['text']):
                msg = 'email_override, send_email, and text must all be set for DOORZETTEN_NAAR_EXTERN flow'
                raise ValidationError({'text': msg})


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
