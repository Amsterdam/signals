# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from datapunt_api.rest import DisplayField, HALSerializer
from rest_framework import serializers

from signals.apps.api.fields import PrivateSignalLinksField
from signals.apps.xperimental.models.signals_filter_view import SignalFilterView


class PrivateSignalSerializerList(HALSerializer):
    serializer_url_field = PrivateSignalLinksField
    _display = DisplayField()

    id = serializers.IntegerField(source='signal_id')

    has_parent = serializers.BooleanField(source='is_child')
    has_children = serializers.BooleanField(source='is_parent')

    status = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    priority = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()

    class Meta:
        model = SignalFilterView
        fields = (
            '_links',
            '_display',
            'id',
            'source',
            'text',
            'text_extra',
            'created_at',
            'updated_at',
            'incident_date_start',
            'incident_date_end',
            'has_parent',
            'has_children',
            'status',
            'location',
            'category',
            'priority',
            'type',
        )
        read_only_fields = fields

    def get_status(self, obj):
        return {
            'state': obj.status_state,
            'state_display': obj.get_status_state_display()
        }

    def get_location(self, obj):
        return {
            'stadsdeel': obj.location_stadsdeel,
            'buurt_code': obj.location_buurt_code,
            'area_type_code': obj.location_area_code_type,
            'area_code': obj.location_area_code,
            'address_text': obj.location_address_text,
        }

    def get_category(self, obj):
        return {
            'main': obj.parent_category_name,
            'main_slug': obj.parent_category_slug,
            'child': obj.child_category_name,
            'sub_slug': obj.child_category_slug,
            'deadline': obj.category_assignment_deadline,
            'deadline_factor_3': obj.category_assignment_deadline_factor_3,
        }

    def get_priority(self, obj):
        return {
            'priority': obj.priority_priority,
        }

    def get_type(self, obj):
        return {
            'code': obj.type_name,
        }
