# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from rest_framework import serializers

from signals.apps.api.generics.serializers import SIAModelSerializer
from signals.apps.api.v1.fields import CategoryHyperlinkedRelatedField
from signals.apps.signals.models import CategoryAssignment


class _NestedCategoryModelSerializer(SIAModelSerializer):
    sub = serializers.CharField(source='category.name', read_only=True)
    sub_slug = serializers.CharField(source='category.slug', read_only=True)
    main = serializers.CharField(source='category.parent.name', read_only=True)
    main_slug = serializers.CharField(source='category.parent.slug', read_only=True)

    sub_category = CategoryHyperlinkedRelatedField(source='category', write_only=True, required=False)
    category_url = CategoryHyperlinkedRelatedField(source='category', required=False)

    text = serializers.CharField(required=False)
    departments = serializers.SerializerMethodField()

    deadline = serializers.DateTimeField(read_only=True)
    deadline_factor_3 = serializers.DateTimeField(read_only=True)

    class Meta:
        model = CategoryAssignment
        fields = (
            'sub_category',
            'sub',
            'sub_slug',
            'main',
            'main_slug',
            'category_url',
            'departments',
            'created_by',
            'text',
            'deadline',
            'deadline_factor_3'
        )
        read_only_fields = (
            'sub',
            'sub_slug',
            'main',
            'main_slug',
            'created_by',
            'departments',
            'deadline',
            'deadline_factor_3'
        )

    def to_internal_value(self, data):
        if 'sub_category' not in data and 'category_url' not in data:
            raise serializers.ValidationError('Either the "sub_category" OR the "category_url" must be given')
        elif 'sub_category' in data and 'category_url' in data:
            raise serializers.ValidationError('Only the "sub_category" OR "category_url" can be given')

        return super(_NestedCategoryModelSerializer, self).to_internal_value(data=data)

    def validate(self, attrs):
        if 'category' not in attrs:
            raise serializers.ValidationError('Either the "sub_category" OR the "category_url" must be given')

        return super(_NestedCategoryModelSerializer, self).validate(attrs=attrs)

    def get_departments(self, obj):
        return ', '.join(
            obj.category.departments.filter(categorydepartment__is_responsible=True).values_list('code', flat=True)
        )
