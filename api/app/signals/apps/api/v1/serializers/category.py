from datapunt_api.rest import DisplayField, HALSerializer
from rest_framework import serializers

from change_log.models import Log
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
    departments = serializers.SerializerMethodField()
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


class PrivateCategoryHistoryHalSerializer(serializers.ModelSerializer):
    identifier = serializers.SerializerMethodField()
    what = serializers.SerializerMethodField()
    action = serializers.ReadOnlyField(source='get_action_display')
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
        return log.get_action_display().upper()

    def get_description(self, log):
        description = []
        for key, value in log.data.items():
            if key == 'name':
                title = f'Naam wijziging'
            elif key == 'description':
                title = f'Omschrijvings wijziging'
            elif key == 'slo':
                title = f'Service level agreement wijziging'

                sla_list = ServiceLevelObjective.objects.filter(pk__in=value)
                sla_value = []
                for sla in sla_list:
                    if sla.use_calendar_days:
                        sla_value.append(f'{sla.n_days} weekdagen')
                    else:
                        sla_value.append(f'{sla.n_days} werkdagen')
                value = '\n'.join(sla_value)
            elif key == 'is_active':
                title = f'Status wijziging'
                value = 'Actief' if value else 'Inactief'
            else:
                continue  # We do not show other tracked values, so on to the next one

            description.append({
                'title': title,
                'text': value
            })
        return description
