from datapunt_api.rest import DisplayField, HALSerializer
from rest_framework.exceptions import ValidationError

from signals.apps.api.v1.fields import StoredSignalFilterLinksField
from signals.apps.api.v1.filters import SignalFilter
from signals.apps.signals.models import Signal, StoredSignalFilter


class StoredSignalFilterSerializer(HALSerializer):
    serializer_url_field = StoredSignalFilterLinksField
    _display = DisplayField()

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
        )

    def validate(self, attrs):
        if 'options' not in attrs:
            raise ValidationError('No filters specified, "options" object missing.')
        signal_filter = SignalFilter(data=attrs['options'], queryset=Signal.objects.none())
        if not signal_filter.is_valid():
            raise ValidationError(signal_filter.errors)

        return super(StoredSignalFilterSerializer, self).validate(attrs)

    def create(self, validated_data):
        validated_data.update({
            'created_by': self.context['request'].user.email
        })
        return super(StoredSignalFilterSerializer, self).create(validated_data=validated_data)
