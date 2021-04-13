# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
from rest_framework.relations import PrimaryKeyRelatedField

from signals.apps.api.generics.serializers import SIAModelSerializer
from signals.apps.signals.models import Department


def _get_department_queryset():
    return Department.objects.all()


class _NestedDepartmentModelSerializer(SIAModelSerializer):
    id = PrimaryKeyRelatedField(required=False, queryset=_get_department_queryset())

    class Meta:
        model = Department
        fields = (
            'id',
            'code',
            'name',
            'is_intern',
        )
        read_only_fields = (
            'id',
            'code',
            'name',
            'is_intern',
        )


class _NestedPublicDepartmentSerializer(SIAModelSerializer):
    class Meta:
        model = Department
        fields = (
            'code',
            'name',
            'is_intern',
        )
        read_only_fields = (
            'code',
            'name',
            'is_intern',
        )
