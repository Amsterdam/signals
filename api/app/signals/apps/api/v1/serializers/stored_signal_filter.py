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

        return super().validate(attrs)

    def validate_options(self, value):
        if type(value) != dict:
            raise ValidationError('Expected an object for "options"')

        signal_filter = SignalFilter(data=value, queryset=Signal.objects.none())
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
        return super(StoredSignalFilterSerializer, self).create(validated_data=validated_data)
