# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from datapunt_api.rest import DisplayField, HALSerializer
from rest_framework import serializers

from change_log.models import Log
from signals.apps.api.fields import (
    CategoryHyperlinkedIdentityField,
    PrivateCategoryHyperlinkedIdentityField
)
from signals.apps.api.serializers.nested import _NestedPublicDepartmentSerializer
from signals.apps.signals.models import Category, CategoryDepartment, ServiceLevelObjective


class CategoryHALSerializer(HALSerializer):
    serializer_url_field = CategoryHyperlinkedIdentityField
    _display = DisplayField()
    departments = serializers.SerializerMethodField()
    questionnaire = serializers.UUIDField(source='questionnaire.uuid', required=False, read_only=True)

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
            'questionnaire',
            'public_name',
        )

    def get_departments(self, obj):
        return _NestedPublicDepartmentSerializer(
            obj.departments.filter(categorydepartment__is_responsible=True),
            many=True
        ).data


class ParentCategoryHALSerializer(HALSerializer):
    serializer_url_field = CategoryHyperlinkedIdentityField
    _display = DisplayField()
    sub_categories = CategoryHALSerializer(many=True, source='children')

    class Meta:
        model = Category
        fields = (
            '_links',
            '_display',
            'name',
            'slug',
            'public_name',
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
    is_intern = serializers.BooleanField(source='department.is_intern')

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

    departments = _NestedPrivateCategoryDepartmentSerializer(source='categorydepartment_set', many=True, read_only=True)

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
            'note',
            'public_name',
            'is_public_accessible',
        )
        read_only_fields = (
            'slug',
        )

    def get_sla(self, obj):
        return PrivateCategorySLASerializer(obj.slo.first()).data

    def update(self, instance, validated_data):
        if 'new_sla' in validated_data:
            new_sla = validated_data.pop('new_sla')
            new_sla.update({'category_id': instance.pk})  # Add the category instance to the new SLA data

            create_new_slo = True
            slo_qs = ServiceLevelObjective.objects.filter(category_id=instance.pk).order_by('-created_at')
            if slo_qs.count() > 0:
                # Check if there are any changes to the SLA data
                latest_slo = slo_qs.first()
                create_new_slo = any([new_sla['n_days'] != latest_slo.n_days,
                                      new_sla['use_calendar_days'] != latest_slo.use_calendar_days])

            if create_new_slo:
                ServiceLevelObjective.objects.create(**new_sla)
                instance.refresh_from_db()

        return super().update(instance, validated_data)


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

    def get_action(self, log):  # noqa C901
        actions = []
        for key, value in log.data.items():
            if key == 'name':
                action = f'Naam gewijzigd naar:\n {value}'
            elif key == 'description':
                action = f'Omschrijving gewijzigd naar:\n {value}'
            elif key == 'slo':
                sla = ServiceLevelObjective.objects.get(pk=value[0])
                action = f'Afhandeltermijn gewijzigd naar:\n {sla.n_days} {"week" if sla.use_calendar_days else "werk"}dagen'  # noqa
            elif key == 'is_active':
                action = f'Status gewijzigd naar:\n {"Actief" if value else "Inactief"}'
            elif key == 'handling_message':
                action = f'Servicebelofte gewijzigd naar:\n {value}'
            elif key == 'public_name':
                action = f'Naam openbaar gewijzigd naar:\n {value}'
            elif key == 'is_public_accessible':
                action = f'Openbaar tonen gewijzigd naar:\n {"Aan" if value else "Uit"}'
            else:
                continue  # We do not show other tracked values, so on to the next one

            actions.append(action)
        return '\n'.join(actions)

    def get_description(self, log):
        return None  # No description implemented yet
