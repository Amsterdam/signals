# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from rest_framework.fields import BooleanField, HiddenField
from rest_framework.serializers import ModelSerializer

from signals.apps.signals.models import Reporter


class ParentSignalDefault:
    requires_context = True

    def __call__(self, serializer_field):
        return serializer_field.context['view'].get_signal()


class SignalReporterSerializer(ModelSerializer):
    _signal = HiddenField(default=ParentSignalDefault())
    allows_contact = BooleanField(source='signal.allows_contact', read_only=True)

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
            '_signal',
        )
        read_only_fields = (
            'id',
            'email_verified',
            'allows_contact',
            'sharing_allowed',
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

    def create(self, validated_data):
        """
        Currently, this method is not implemented. It should create a new
        Reporter instance. However, all state machine logic still needs to
        be implemented. Therefore, a dummy Reporter instance is returned.

        TODO: Correctly implement the logic needed to create new Reporter
              instances.
        """
        return Reporter(**validated_data, pk=0)
