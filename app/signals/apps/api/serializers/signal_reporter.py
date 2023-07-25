# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from rest_framework.fields import BooleanField
from rest_framework.serializers import ModelSerializer

from signals.apps.signals.models import Reporter, Signal


class SignalReporterSerializer(ModelSerializer):
    allows_contact = BooleanField(source='_signal.allows_contact', read_only=True)
    sharing_allowed = BooleanField(required=True)

    class Meta:
        model = Reporter
        fields = (
            'id',
            'email',
            'phone',
            'allows_contact',
            'sharing_allowed',
            'state',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'email_verified',
            'allows_contact',
            'state',
            'created_at',
            'updated_at',
        )

    def to_representation(self, instance: Reporter) -> dict:
        serialized = super().to_representation(instance)

        user = self.context['request'].user if 'request' in self.context else None
        if not user or not user.has_perm('signals.sia_can_view_contact_details'):
            serialized['email'] = '*****' if serialized['email'] else ''
            serialized['phone'] = '*****' if serialized['phone'] else ''

        return serialized

    def create(self, validated_data: dict) -> Reporter:
        signal_id = self.context['view'].kwargs.get('parent_lookup__signal_id')
        signal = Signal.objects.get(pk=signal_id)

        reporter = Reporter()
        reporter.email = validated_data.get('email')
        reporter.phone = validated_data.get('phone')
        reporter.sharing_allowed = validated_data.get('sharing_allowed')
        reporter._signal = signal
        reporter.save()

        return reporter
