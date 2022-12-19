# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2022 Gemeente Amsterdam
from rest_framework import serializers

from signals.apps.signals.models import Department
from signals.apps.users.models import Profile


def _get_departments_queryset():
    return Department.objects.all()


class ProfileListSerializer(serializers.ModelSerializer):
    departments = serializers.SerializerMethodField()
    department_ids = serializers.PrimaryKeyRelatedField(
        many=True, required=False, read_only=False, write_only=True,
        queryset=_get_departments_queryset(), source='departments'
    )

    class Meta:
        model = Profile
        fields = (
            'note',
            'departments',
            'department_ids',
            'created_at',
            'updated_at',
        )

    def get_departments(self, obj):
        return obj.departments.values_list('name', flat=True)


class ProfileDetailSerializer(serializers.ModelSerializer):
    departments = serializers.SerializerMethodField()
    department_ids = serializers.PrimaryKeyRelatedField(
        many=True, required=False, read_only=False, write_only=True,
        queryset=_get_departments_queryset(), source='departments'
    )
    categories = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = (
            'note',
            'departments',
            'department_ids',
            'categories',
            'created_at',
            'updated_at',
        )

    def get_departments(self, obj):
        return obj.departments.values_list('name', flat=True)

    def get_categories(self, obj):
        from signals.apps.signals.models import Category

        if self.context['request'].user.is_superuser:
            category_qs = Category.objects.all()
        else:
            category_qs = Category.objects.filter(departments__code__in=obj.departments.values_list('code', flat=True))
        return category_qs.exclude(parent__isnull=True).values_list('slug', flat=True)
