# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2023 Gemeente Amsterdam
from datapunt_api.rest import DisplayField, HALSerializer
from rest_framework.exceptions import ValidationError

from signals.apps.api.fields import StoredSignalFilterLinksField
from signals.apps.api.filters import SignalFilterSet
from signals.apps.signals.models import Signal, StoredSignalFilter


class StoredSignalFilterSerializer(HALSerializer):
    serializer_url_field = StoredSignalFilterLinksField
    _display: DisplayField = DisplayField()

    class Meta:
        model = StoredSignalFilter
        fields = (
            '_links',
            '_display',
            'id',
            'name',
            'created_at',
            'options',
            'refresh',
            'show_on_overview',
        )

    def validate(self, attrs):
        if 'options' not in attrs and self.context['view'].action != 'partial_update':
            """
            When doing a partial_update the "options" are not mandatory, for all other actions they are!
            """
            raise ValidationError('No filters specified, "options" object missing.')

        return super().validate(attrs)

    def validate_options(self, value):
        if not isinstance(value, dict):
            raise ValidationError('Expected an object for "options"')

        signal_filter = SignalFilterSet(data=value, queryset=Signal.objects.none())
        if not signal_filter.is_valid():
            raise ValidationError(signal_filter.errors)

        # Check that we are only accepting filter data for which there are
        # actual Filter definitions on the SignalFilter FilterSet (SIG-2322).
        filter_names = set(signal_filter.get_filters())
        undefined_filters = set(value) - filter_names
        if undefined_filters:
            raise ValidationError('FilterSet data to store contains unknown filters {}'.format(
                repr(list(undefined_filters))
            ))

        return value

    def create(self, validated_data):
        validated_data.update({
            'created_by': self.context['request'].user.email
        })
        return super().create(validated_data=validated_data)
