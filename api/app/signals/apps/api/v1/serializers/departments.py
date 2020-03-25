from datapunt_api.rest import DisplayField, HALSerializer
from rest_framework import serializers

from signals.apps.api.v0.serializers import _NestedDepartmentSerializer
from signals.apps.api.v1.fields import (
    CategoryHyperlinkedIdentityField,
    ParentCategoryHyperlinkedIdentityField
)
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
    """
    TODO: Refactor the TemporaryCategoryHALSerializer and TemporaryParentCategoryHALSerializer serializers
    """
    serializer_url_field = CategoryHyperlinkedIdentityField
    _display = DisplayField()
    departments = serializers.SerializerMethodField()

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

    def get_departments(self, obj):
        return _NestedDepartmentSerializer(
            obj.departments.filter(categorydepartment__is_responsible=True),
            many=True
        ).data


class TemporaryParentCategoryHALSerializer(TemporaryCategoryHALSerializer):
    """
    SIG-2287 [BE] Afdeling geeft categorie zonder main slug terug

    Added a TemporaryParentCategoryHALSerializer so that we can override the serializer_url_field to render the correct
    url for a parent category

    TODO: Refactor the TemporaryCategoryHALSerializer and TemporaryParentCategoryHALSerializer serializers
    """
    serializer_url_field = ParentCategoryHyperlinkedIdentityField


class CategoryDepartmentSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()
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

    def get_category(self, obj):
        """
        SIG-2287 [BE] Afdeling geeft categorie zonder main slug terug

        The category was rendered as if it was a child category. So when encountering a parent category the link results
        in a link with the parent category slug as "None". So before rendering the correct serializer we need to check
        if we have a parent or a child category.

        TODO: When refactoring the TemporaryCategoryHALSerializer and TemporaryParentCategoryHALSerializer serializers
              we also need to take a look at a better solution for this issue.
        """
        if obj.category.is_parent():
            serializer_class = TemporaryParentCategoryHALSerializer
        else:
            serializer_class = TemporaryCategoryHALSerializer
        return serializer_class(obj.category, context=self.context).data


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
