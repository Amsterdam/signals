from datapunt_api.rest import DisplayField, HALSerializer
from rest_framework import serializers

from signals.apps.api.v0.serializers import _NestedDepartmentSerializer
from signals.apps.api.v1.fields import CategoryHyperlinkedIdentityField
from signals.apps.email_integrations.core.messages import \
    ALL_AFHANDELING_TEXT  # noqa TODO: move to a model
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
        return list(obj.category_set.filter(is_active=True).values_list('name', flat=True))


def _get_categories_queryset():
    return Category.objects.filter(is_active=True)


class TemporaryCategoryHALSerializer(HALSerializer):
    serializer_url_field = CategoryHyperlinkedIdentityField
    _display = DisplayField()
    departments = serializers.SerializerMethodField()
    handling_message = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = (
            '_links',
            '_display',
            'id',
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


class CategoryDepartmentSerializer(serializers.ModelSerializer):
    category = TemporaryCategoryHALSerializer(read_only=True, required=False)
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

    categories = CategoryDepartmentSerializer(source='active_categorydepartment_set',
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
        if 'active_categorydepartment_set' in validated_data:
            categorydepartment_set_validated_data = validated_data.pop('active_categorydepartment_set')

        instance = super(PrivateDepartmentSerializerDetail, self).create(validated_data)

        if categorydepartment_set_validated_data:
            self._save_category_department(
                instance=instance,
                validated_data=categorydepartment_set_validated_data
            )

        instance.refresh_from_db()
        return instance

    def update(self, instance, validated_data):
        if 'active_categorydepartment_set' in validated_data:
            self._save_category_department(
                instance=instance,
                validated_data=validated_data.pop('active_categorydepartment_set')
            )

        instance = super(PrivateDepartmentSerializerDetail, self).update(instance, validated_data)
        instance.refresh_from_db()
        return instance
