# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2023 Gemeente Amsterdam
from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from signals.apps.signals.models import Category


class _SimpleCategorySerializer(serializers.Serializer):
    name = serializers.CharField()
    departments = serializers.SerializerMethodField(method_name='get_departments')

    def get_departments(self, obj: Category) -> list[str]:
        return list(obj.categorydepartment_set.filter(
            is_responsible=True
        ).values_list(
            'department__code',
            flat=True
        ).order_by('department__code'))


class _SignalsPerCategoryCount(serializers.Serializer):
    category = serializers.SerializerMethodField()
    signal_count = serializers.IntegerField(source='per_category_count')

    @extend_schema_field(_SimpleCategorySerializer)
    def get_category(self, obj: dict) -> dict:
        category = Category.objects.get(id=obj['category_assignment__category_id'])
        serializer = _SimpleCategorySerializer(category, context=self.context)
        return serializer.data


class ReportSignalsPerCategory(serializers.Serializer):
    total_signal_count = serializers.SerializerMethodField()
    results = serializers.SerializerMethodField()

    @extend_schema_field(_SignalsPerCategoryCount)
    def get_results(self, obj: dict) -> dict:
        serializer = _SignalsPerCategoryCount(obj, many=True, context=self.context)
        return serializer.data

    def get_total_signal_count(self, obj: QuerySet) -> int:
        return sum(obj.values_list('per_category_count', flat=True))
