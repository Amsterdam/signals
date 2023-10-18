# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2023 Gemeente Amsterdam
from django.db.models import QuerySet
from rest_framework import serializers

from signals.apps.signals.models import Department
from signals.apps.users.models import Profile


def _get_departments_queryset() -> QuerySet[Department]:
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

    def get_departments(self, obj: Profile) -> list[str]:
        return list(obj.departments.values_list('name', flat=True))


class ProfileDetailSerializer(serializers.ModelSerializer):
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
            'notification_on_user_assignment',
            'notification_on_department_assignment',
        )

    def get_departments(self, obj: Profile) -> list[str]:
        return list(obj.departments.values_list('name', flat=True))
