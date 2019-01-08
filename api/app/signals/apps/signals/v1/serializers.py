"""
Serializsers that are used exclusively by the V1 API
"""
from datapunt_api.rest import DisplayField, HALSerializer
from rest_framework import serializers

from signals.apps.signals.api_generics.mixins import AddExtrasMixin
from signals.apps.signals.api_generics.validators import NearAmsterdamValidatorMixin
from signals.apps.signals.models import (
    History,
    Location,
    MainCategory,
    Signal,
    SubCategory,
)
from signals.apps.signals.v0.serializers import _NestedDepartmentSerializer  # TODO: ../generic/.. ?
from signals.apps.signals.v1.fields import (
    MainCategoryHyperlinkedIdentityField,
    PrivateSignalLinksField,
    PrivateSignalLinksFieldWithArchives,
    SubCategoryHyperlinkedIdentityField,
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

# -- serializers related to /signals/private/signals/ --

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

# -- serializers related to /signals/private/signals/<pk> --

class _NestedLocationModelSerializer(NearAmsterdamValidatorMixin, serializers.ModelSerializer):

    class Meta:
        model = Location
        geo_field = 'geometrie'
        fields = (
            'id',
            'stadsdeel',
            'buurt_code',
            'address',
            'address_text',
            'geometrie',
            'extra_properties',
        )
        read_only_fields = (
            'id',
        )
        extra_kwargs = {
            'id': {'label': 'ID', },
        }


class PrivateSignalSerializerDetail(HALSerializer):
    serializer_url_field = PrivateSignalLinksFieldWithArchives
    _display = DisplayField()
    image = serializers.ImageField(read_only=True)
    location = _NestedLocationModelSerializer()

    class Meta:
        model = Signal
        fields = (
            '_links',
            '_display',
            'id',
            'image',
            'location',
        )
