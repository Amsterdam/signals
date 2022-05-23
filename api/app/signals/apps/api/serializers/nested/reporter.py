# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2022 Gemeente Amsterdam
from rest_framework import serializers

from signals.apps.api.generics.serializers import SIAModelSerializer
from signals.apps.signals.models import Reporter


class _NestedReporterModelSerializer(SIAModelSerializer):

    allows_contact = serializers.BooleanField(source='_signal.allows_contact', read_only=True)

    class Meta:
        model = Reporter
        fields = (
            'email',
            'phone',
            'sharing_allowed',
            'allows_contact'
        )

    def to_representation(self, instance):
        """
        For backwards compatibility we replace null in email and phone fields with empty string.
        """
        serialized = super().to_representation(instance)

        user = self.context['request'].user if 'request' in self.context else None
        if not user or not user.has_perm('signals.sia_can_view_contact_details'):
            serialized['email'] = '*****' if serialized['email'] else ''
            serialized['phone'] = '*****' if serialized['phone'] else ''
        else:
            serialized['email'] = serialized['email'] if serialized['email'] else ''
            serialized['phone'] = serialized['phone'] if serialized['phone'] else ''

        return serialized

    def to_internal_value(self, data):
        """
        For backwards compatibility we replace empty string in email and phone fields with null.
        """
        if 'email' in data and data['email'] == '':
            data['email'] = None
        if 'phone' in data and data['phone'] == '':
            data['phone'] = None

        return super().to_internal_value(data)
