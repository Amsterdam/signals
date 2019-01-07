"""
Serializsers that are used exclusively by the V1 API
"""
from datapunt_api.rest import DisplayField, HALSerializer
from rest_framework import serializers

from signals.apps.signals.api_generics.mixins import AddExtrasMixin
from signals.apps.signals.models import (
    CategoryAssignment,
    History,
    Location,
    MainCategory,
    Note,
    Priority,
    Signal,
    SubCategory,
    Status
)
from signals.apps.signals.v0.serializers import _NestedDepartmentSerializer  # TODO: ../generic/.. ?
from signals.apps.signals.v1.fields import (
    MainCategoryHyperlinkedIdentityField,
    PrivateSignalLinksField,
    PrivateSignalLinksFieldWithArchives,
    SubCategoryHyperlinkedIdentityField,
    SubCategoryHyperlinkedRelatedField,
)
from signals.apps.signals import workflow

# -- /public API serializers --

class SubCategoryHALSerializer(HALSerializer):
    serializer_url_field = SubCategoryHyperlinkedIdentityField
    _display = DisplayField()
    departments = _NestedDepartmentSerializer(many=True)

    class Meta:
        model = SubCategory
        fields = (
            '_links',
            '_display',
            'name',
            'slug',
            'handling',
            'departments',
            'is_active',
        )


class MainCategoryHALSerializer(HALSerializer):
    serializer_url_field = MainCategoryHyperlinkedIdentityField
    _display = DisplayField()
    sub_categories = SubCategoryHALSerializer(many=True)

    class Meta:
        model = MainCategory
        fields = (
            '_links',
            '_display',
            'name',
            'slug',
            'sub_categories',
        )


# -- /private API serializers --

class HistoryHalSerializer(HALSerializer):
    _signal = serializers.PrimaryKeyRelatedField(queryset=Signal.objects.all())
    who = serializers.SerializerMethodField()

    def get_who(self, obj):
        """Generate string to show in UI, missing users are set to default."""
        if obj.who is None:
            return 'SIA systeem'
        return obj.who

    class Meta:
        model = History
        fields = (
            'identifier',
            'when',
            'what',
            'action',
            'description',
            'who',
            '_signal',
        )


class CategoryHALSerializer(HALSerializer):
    # Should be required, but to make it work with the backwards compatibility fix it's not required
    # at the moment..
    sub = serializers.CharField(source='sub_category.name', read_only=True)
    sub_slug = serializers.CharField(source='sub_category.slug', read_only=True)
    main = serializers.CharField(source='sub_category.main_category.name', read_only=True)
    main_slug = serializers.CharField(source='sub_category.main_category.slug', read_only=True)

    # Backwards compatibility fix for departments, should be retrieved from category terms resource.
    department = serializers.SerializerMethodField(source='sub_category.departments',
                                                   read_only=True)

    class Meta(object):
        model = CategoryAssignment
        fields = (
            'sub',
            'sub_slug',
            'main',
            'main_slug',
            'department',
            'created_by',
            'created_at',
        )

    def get_department(self, obj):
        return ', '.join(obj.sub_category.departments.values_list('code', flat=True))


class StatusHALSerializer(HALSerializer):
    state_display = serializers.CharField(source='get_state_display', read_only=True)

    class Meta(object):
        model = Status
        fields = (
            'text',
            'user',
            'target_api',
            'state',
            'state_display',
            'extra_properties',
            'created_at',
        )


class LocationHALSerializer(HALSerializer):

    class Meta:
        model = Location
        fields = (
            'id',
            'stadsdeel',
            'buurt_code',
            'address',
            'geometrie',
            'created_by',
            'extra_properties',
            'created_at',
        )


class PriorityHALSerializer(HALSerializer):

    class Meta:
        model = Priority
        fields = (
            'id',
            'priority',
            'created_at',
            'created_by',
        )


class NoteHALSerializer(HALSerializer):

    class Meta:
        model = Note
        fields = (
            'text',
            'created_at',
            'created_by',
        )


class PrivateSignalSerializerDetail(HALSerializer):
    serializer_url_field = PrivateSignalLinksFieldWithArchives
    _display = DisplayField()
    image = serializers.ImageField(read_only=True)

    class Meta:
        model = Signal
        fields = (
            '_links',
            '_display',
            'id',
            'image',
        )


class PrivateSignalSerializerList(HALSerializer):
    serializer_url_field = PrivateSignalLinksField
    _display = DisplayField()

    class Meta:
        model = Signal
        fields = (
            '_links',
            '_display',
            'id',
        )
