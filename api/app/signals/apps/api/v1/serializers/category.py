from datapunt_api.rest import DisplayField, HALSerializer
from rest_framework import serializers

from change_log.models import Log
from signals.apps.api.v0.serializers import _NestedDepartmentSerializer
from signals.apps.api.v1.fields import (
    CategoryHyperlinkedIdentityField,
    ParentCategoryHyperlinkedIdentityField,
    PrivateCategoryHyperlinkedIdentityField
)
from signals.apps.signals.models import Category, CategoryDepartment, ServiceLevelObjective


class CategoryHALSerializer(HALSerializer):
    serializer_url_field = CategoryHyperlinkedIdentityField
    _display = DisplayField()
    departments = serializers.SerializerMethodField()

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

    def get_departments(self, obj):
        return _NestedDepartmentSerializer(
            obj.departments.filter(categorydepartment__is_responsible=True),
            many=True
        ).data


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


class _NestedPrivateCategoryDepartmentSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='department.id')
    code = serializers.CharField(source='department.code')
    name = serializers.CharField(source='department.name')
    is_intern = serializers.CharField(source='department.is_intern')

    class Meta:
        model = CategoryDepartment
        fields = (
            'id',
            'code',
            'name',
            'is_intern',
            'is_responsible',
            'can_view',
        )
        read_only_fields = fields


class PrivateCategorySerializer(HALSerializer):
    serializer_url_field = PrivateCategoryHyperlinkedIdentityField
    _display = DisplayField()
    sla = serializers.SerializerMethodField()
    new_sla = PrivateCategorySLASerializer(write_only=True)

    departments = serializers.SerializerMethodField()

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
            'departments',
        )
        read_only_fields = (
            'id',
            'slug',
            'sla',
            'departments',  # noqa Is read-only by default because we use the SerializerMethodField but also added here for readability
        )

    def get_sla(self, obj):
        return PrivateCategorySLASerializer(obj.slo.all().order_by('-created_at').first()).data

    def get_departments(self, obj):
        return _NestedPrivateCategoryDepartmentSerializer(
            CategoryDepartment.objects.filter(category_id=obj.pk).order_by('department__code'),
            many=True
        ).data

    def update(self, instance, validated_data):
        new_sla = validated_data.pop('new_sla') if 'new_sla' in validated_data else None
        if new_sla:
            ServiceLevelObjective.objects.create(category=instance, **new_sla)
            instance.refresh_from_db()

        return super(PrivateCategorySerializer, self).update(instance, validated_data)


class PrivateCategoryHistoryHalSerializer(serializers.ModelSerializer):
    identifier = serializers.SerializerMethodField()
    what = serializers.SerializerMethodField()
    action = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    _category = serializers.IntegerField(source='object_id', read_only=True)

    class Meta:
        model = Log
        fields = (
            'identifier',
            'when',
            'what',
            'action',
            'description',
            'who',
            '_category',
        )

    def get_identifier(self, log):
        return f'{log.get_action_display().upper()}_CATEGORY_{log.id}'

    def get_what(self, log):
        return f'{log.get_action_display().upper()}_CATEGORY'

    def get_action(self, log):
        actions = []
        for key, value in log.data.items():
            if key == 'name':
                action = f'Naam wijziging:\n {value}'
            elif key == 'description':
                action = f'Omschrijvings wijziging:\n {value}'
            elif key == 'slo':
                sla = ServiceLevelObjective.objects.get(pk=value[0])
                action = f'Service level agreement wijziging:\n {sla.n_days} {"week" if sla.use_calendar_days else "werk"}dagen'  # noqa
            elif key == 'is_active':
                action = f'Status wijziging:\n {"Actief" if value else "Inactief"}'
            elif key == 'handling_message':
                action = f'E-mail tekst wijziging:\n {value}'
            else:
                continue  # We do not show other tracked values, so on to the next one

            actions.append(action)
        return f'\n'.join(actions)

    def get_description(self, log):
        return None  # No description implemented yet
