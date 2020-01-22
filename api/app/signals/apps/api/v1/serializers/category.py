from datapunt_api.rest import DisplayField, HALSerializer
from rest_framework import serializers

from signals.apps.api.v0.serializers import _NestedDepartmentSerializer
from signals.apps.api.v1.fields import (
    CategoryHyperlinkedIdentityField,
    ParentCategoryHyperlinkedIdentityField,
    PrivateCategoryHyperlinkedIdentityField
)
from signals.apps.email_integrations.core.messages import \
    ALL_AFHANDELING_TEXT  # noqa TODO: move to a model
from signals.apps.signals.models import Category, ServiceLevelObjective


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
            'description',
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


class PrivateCategorySLASerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceLevelObjective
        fields = (
            'n_days',
            'use_calendar_days',
        )


class PrivateCategorySerializer(HALSerializer):
    serializer_url_field = PrivateCategoryHyperlinkedIdentityField
    _display = DisplayField()
    handling_message = serializers.SerializerMethodField()
    sla = serializers.SerializerMethodField()
    new_sla = PrivateCategorySLASerializer(write_only=True)

    class Meta:
        model = Category
        fields = (
            '_links',
            '_display',
            'id',
            'name',
            'slug',
            'is_active',
            'description',
            'handling_message',
            'sla',
            'new_sla',
        )
        read_only_fields = (
            'id',
            'slug',
            'handling_message',
            'sla',
        )

    def get_handling_message(self, obj):
        return ALL_AFHANDELING_TEXT[obj.handling]

    def get_sla(self, obj):
        return PrivateCategorySLASerializer(obj.slo.all().order_by('-created_at').first()).data

    def update(self, instance, validated_data):
        new_sla = validated_data.pop('new_sla') if 'new_sla' in validated_data else None
        if new_sla:
            ServiceLevelObjective.objects.create(category=instance, **new_sla)
            instance.refresh_from_db()

        return super(PrivateCategorySerializer, self).update(instance, validated_data)
