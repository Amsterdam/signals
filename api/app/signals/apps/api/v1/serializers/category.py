from datapunt_api.rest import DisplayField, HALSerializer
from rest_framework import serializers

from signals.apps.api.v0.serializers import _NestedDepartmentSerializer
from signals.apps.api.v1.fields import (
    CategoryHyperlinkedIdentityField,
    ParentCategoryHyperlinkedIdentityField
)
from signals.apps.email_integrations.messages import ALL_AFHANDELING_TEXT  # TODO: move to a model
from signals.apps.signals.models import Category


class CategoryHALSerializer(HALSerializer):
    serializer_url_field = CategoryHyperlinkedIdentityField
    _display = DisplayField()
    departments = _NestedDepartmentSerializer(many=True)
    handling_message = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = (
            '_links',
            '_display',
            'name',
            'slug',
            'handling',
            'departments',
            'is_active',
            'handling_message',
        )

    def get_handling_message(self, obj):
        return ALL_AFHANDELING_TEXT[obj.handling]


class ParentCategoryHALSerializer(HALSerializer):
    serializer_url_field = ParentCategoryHyperlinkedIdentityField
    _display = DisplayField()
    sub_categories = CategoryHALSerializer(many=True, source='children')

    class Meta:
        model = Category
        fields = (
            '_links',
            '_display',
            'name',
            'slug',
            'sub_categories',
        )
