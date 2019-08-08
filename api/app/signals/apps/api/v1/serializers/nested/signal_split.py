from datapunt_api.rest import HALSerializer
from rest_framework import serializers

from signals.apps.api.v1.fields import PrivateSignalLinksField
from signals.apps.api.v1.serializers.nested import _NestedCategoryModelSerializer
from signals.apps.signals.models import Signal


class _NestedSplitSignalSerializer(HALSerializer):
    serializer_url_field = PrivateSignalLinksField
    reuse_parent_image = serializers.BooleanField(default=False, write_only=True)
    category = _NestedCategoryModelSerializer(required=True, source='category_assignment')

    class Meta:
        model = Signal
        fields = (
            'id',
            'text',
            'reuse_parent_image',
            'category',
            '_links',
        )
        read_only_fields = (
            'id',
            '_links',
        )
