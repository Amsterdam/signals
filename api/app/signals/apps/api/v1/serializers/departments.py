from datapunt_api.rest import DisplayField, HALSerializer
from rest_framework import serializers

from signals.apps.api.v1.serializers import CategoryHALSerializer
from signals.apps.signals.models import Category, CategoryDepartment, Department


class PrivateDepartmentSerializerList(HALSerializer):
    _display = DisplayField()
    category_names = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = (
            '_links',
            '_display',
            'id',
            'name',
            'code',
            'is_intern',
            'category_names',
        )

    def get_category_names(self, obj):
        return list(obj.category_set.values_list('name', flat=True))


def _get_categories_queryset():
    return Category.objects.filter(is_active=True)


class CategoryDepartmentSerializer(serializers.ModelSerializer):
    category = CategoryHALSerializer(read_only=True, required=False)
    category_id = serializers.PrimaryKeyRelatedField(
        required=True, read_only=False, write_only=True,
        queryset=_get_categories_queryset(), source='category'
    )

    class Meta:
        model = CategoryDepartment
        fields = (
            'id',
            'category',
            'category_id',
            'is_responsible',
            'can_view',
        )


class PrivateDepartmentSerializerDetail(HALSerializer):
    _display = DisplayField()

    categories = CategoryDepartmentSerializer(source='categorydepartment_set',
                                              many=True,
                                              required=False)

    class Meta:
        model = Department
        fields = (
            '_links',
            '_display',
            'id',
            'name',
            'code',
            'is_intern',
            'categories',
        )

    def _save_category_department(self, instance, validated_data):
        instance.category_set.clear()
        for category_department_validated_data in validated_data:
            category_department_validated_data['department'] = instance
            category_department = CategoryDepartment(**category_department_validated_data)
            category_department.save()

    def create(self, validated_data):
        categorydepartment_set_validated_data = None
        if 'categorydepartment_set' in validated_data:
            categorydepartment_set_validated_data = validated_data.pop('categorydepartment_set')

        instance = super(PrivateDepartmentSerializerDetail, self).create(validated_data)

        if categorydepartment_set_validated_data:
            self._save_category_department(
                instance=instance,
                validated_data=categorydepartment_set_validated_data
            )

        instance.refresh_from_db()
        return instance

    def update(self, instance, validated_data):
        if 'categorydepartment_set' in validated_data:
            self._save_category_department(
                instance=instance,
                validated_data=validated_data.pop('categorydepartment_set')
            )

        instance = super(PrivateDepartmentSerializerDetail, self).update(instance, validated_data)
        instance.refresh_from_db()
        return instance
