"""
Serializsers that are used exclusively by the V0 API
"""
import logging
import os

from datapunt_api.rest import DisplayField, HALSerializer
from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from signals.apps.api.app_settings import SIGNALS_API_MAX_UPLOAD_SIZE
from signals.apps.api.generics.mixins import AddExtrasMixin, NearAmsterdamValidatorMixin
from signals.apps.api.v0.fields import (
    CategoryLinksField,
    PriorityLinksField,
    SignalLinksField,
    SignalUnauthenticatedLinksField,
    StatusLinksField
)
from signals.apps.api.v1.fields import (
    LegacyCategoryHyperlinkedRelatedField,
    NoteHyperlinkedIdentityField
)
from signals.apps.api.v1.validators.extra_properties import ExtraPropertiesValidator
from signals.apps.signals import workflow
from signals.apps.signals.models import (
    Category,
    CategoryAssignment,
    Department,
    Location,
    Note,
    Priority,
    Reporter,
    Signal,
    Status
)

logger = logging.getLogger(__name__)


class SignalUpdateImageSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(label='ID', read_only=True)
    signal_id = serializers.CharField(label='SIGNAL_ID')

    class Meta(object):
        model = Signal
        fields = (
            'id',
            'signal_id',
            'image',
        )

    def create(self, validated_data):
        signal_id = validated_data.get('signal_id')
        instance = Signal.objects.get(signal_id=signal_id)
        return self.update(instance, validated_data)

    def _image_attachment_exists(self):
        signal_id = self.initial_data.get('signal_id')
        signal = Signal.objects.get(signal_id=signal_id)
        image_attachments = signal.attachments.filter(is_image=True)

        return len(image_attachments) > 0

    def validate(self, attrs):
        if self._image_attachment_exists():
            raise PermissionDenied("Melding is reeds van foto voorzien")

        image = self.initial_data.get('image', False)
        if image:
            if image.size > SIGNALS_API_MAX_UPLOAD_SIZE:
                msg = f'Bestand mag maximaal {SIGNALS_API_MAX_UPLOAD_SIZE} bytes groot zijn.'
                raise ValidationError(msg)
        else:
            raise ValidationError("Foto is een verplicht veld.")

        attrs['image'] = image
        return attrs

    def update(self, instance, validated_data):
        image = validated_data['image']

        # Only allow adding a photo if none is set.
        if instance.image:
            raise PermissionDenied("Melding is reeds van foto voorzien.")

        if image:
            Signal.actions.add_image(image, instance)

        return instance


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
            'bag_validated',
        )
        read_only_fields = (
            'id',
            'bag_validated',
        )
        extra_kwargs = {
            'id': {'label': 'ID', },
        }


class _NestedStatusModelSerializer(serializers.ModelSerializer):
    state_display = serializers.CharField(source='get_state_display', read_only=True)

    class Meta:
        model = Status
        fields = (
            'text',
            'user',
            'state',
            'state_display',
            'extra_properties',
            'created_at',
        )
        read_only_fields = (
            'state',
            'created_at',
        )


class _NestedCategoryModelSerializer(serializers.ModelSerializer):
    # Should be required, but to make it work with the backwards compatibility fix it's not required
    # at the moment..
    sub_category = LegacyCategoryHyperlinkedRelatedField(write_only=True, required=False,
                                                         source='category')

    sub = serializers.CharField(source='category.name', read_only=True)
    sub_slug = serializers.CharField(source='category.slug', read_only=True)
    main = serializers.CharField(source='category.parent.name', read_only=True)
    main_slug = serializers.CharField(source='category.parent.slug', read_only=True)

    category_url = serializers.SerializerMethodField(read_only=True)

    # Backwards compatibility fix for departments, should be retrieved from category terms resource.
    department = serializers.SerializerMethodField(source='category.departments',
                                                   read_only=True)

    class Meta:
        model = CategoryAssignment
        fields = (
            'category_url',
            'sub',
            'sub_slug',
            'main',
            'main_slug',
            'sub_category',
            'department',
        )

    def get_department(self, obj):
        return ', '.join(obj.category.departments.values_list('code', flat=True))

    def to_internal_value(self, data):
        internal_data = super().to_internal_value(data)

        if 'sub_category' in data:
            # Fix for renaming sub_category to category internally
            data['category'] = data['sub_category']
            del data['sub_category']

        # Backwards compatibility fix to let this endpoint work with `sub` as key.
        is_main_name_posted = 'main' in data
        is_sub_name_posted = 'sub' in data
        is_category_not_posted = 'category' not in data
        if is_main_name_posted and is_sub_name_posted and is_category_not_posted:
            try:
                category = Category.objects.get(parent__name__iexact=data['main'],
                                                name__iexact=data['sub'])
            except Category.DoesNotExist:
                internal_data['category'] = Category.objects.get(id=76)  # Overig
            else:
                internal_data['category'] = category

        return internal_data

    def get_category_url(self, obj):
        from rest_framework.reverse import reverse
        request = self.context['request'] if 'request' in self.context else None
        return reverse(
            'v1:category-detail',
            kwargs={
                'slug': obj.category.parent.slug,
                'sub_slug': obj.category.slug,
            },
            request=request
        )


class _NestedReporterModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reporter
        fields = (
            'email',
            'phone',
        )


class _NestedPriorityModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Priority
        fields = (
            'priority',
        )


#
# Unauth serializers
#


class SignalCreateSerializer(serializers.ModelSerializer):
    location = _NestedLocationModelSerializer()
    reporter = _NestedReporterModelSerializer()
    status = _NestedStatusModelSerializer()
    category = _NestedCategoryModelSerializer(source='category_assignment')
    priority = _NestedPriorityModelSerializer(required=False, read_only=True)
    image = serializers.ImageField(source='image_crop', read_only=True)

    incident_date_start = serializers.DateTimeField()

    class Meta(object):
        model = Signal
        fields = (
            'id',
            'signal_id',
            'source',
            'image',
            'text',
            'text_extra',
            'status',
            'location',
            'category',
            'reporter',
            'priority',
            'created_at',
            'updated_at',
            'incident_date_start',
            'incident_date_end',
            'operational_date',
            'extra_properties',
        )
        read_only_fields = (
            'id',
            'signal_id',
            'created_at',
            'updated_at',
        )
        extra_kwargs = {
            'id': {'label': 'ID'},
            'signal_id': {'label': 'SIGNAL_ID'},

            # Because we want to disable V0 on short term we use the V1 validator for now
            'extra_properties': {'validators': [ExtraPropertiesValidator(filename=os.path.join(os.path.dirname(__file__), '..', 'v1', 'json_schema', 'extra_properties.json'))]},  # noqa
        }

    def create(self, validated_data):
        status_data = validated_data.pop('status')
        location_data = validated_data.pop('location')
        reporter_data = validated_data.pop('reporter')
        category_assignment_data = validated_data.pop('category_assignment')

        image = validated_data.pop('image', None)

        signal = Signal.actions.create_initial(
            validated_data, location_data, status_data, category_assignment_data, reporter_data)

        if image:
            Signal.actions.add_image(image, signal)

        return signal

    def validate(self, data):
        image = self.initial_data.get('image', False)
        if image:
            if image.size > 8388608:  # 8MB = 8*1024*1024
                raise ValidationError("Maximum photo size is 8Mb.")

        if image:
            data['image'] = image

        return data


class _NestedStatusUnauthenticatedModelSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(label='ID', read_only=True)

    class Meta:
        model = Status
        fields = (
            'id',
            'state',
        )
        extra_kwargs = {
            '_signal': {'required': False},
        }


class SignalStatusOnlyHALSerializer(HALSerializer):
    _display = DisplayField()
    signal_id = serializers.CharField(label='SIGNAL_ID', read_only=True)
    status = _NestedStatusUnauthenticatedModelSerializer(read_only=True)

    _links = SignalUnauthenticatedLinksField('signal-detail')

    class Meta(object):
        model = Signal
        fields = (
            '_links',
            '_display',
            'signal_id',
            'status',
            'created_at',
            'updated_at',
            'incident_date_start',
            'incident_date_end',
            'operational_date',
        )
        read_only_fields = (
            'created_at',
            'updated_at',
        )


#
# Auth serializers
#

class SignalAuthHALSerializerList(HALSerializer):
    """Read-only serializer for lists of `Signal` objects."""
    _display = DisplayField()
    id = serializers.IntegerField(label='ID', read_only=True)
    signal_id = serializers.CharField(label='SIGNAL_ID', read_only=True)
    location = _NestedLocationModelSerializer(read_only=True)
    reporter = _NestedReporterModelSerializer(read_only=True)
    status = _NestedStatusModelSerializer(read_only=True)
    category = _NestedCategoryModelSerializer(source='category_assignment', read_only=True)
    priority = _NestedPriorityModelSerializer(read_only=True)
    notes_count = serializers.SerializerMethodField()

    parent_id = serializers.IntegerField(read_only=True)
    child_ids = serializers.SerializerMethodField(read_only=True)

    serializer_url_field = SignalLinksField

    def get_notes_count(self, obj):
        return obj.notes.count()

    class Meta(object):
        model = Signal
        fields = (
            '_links',
            '_display',
            'id',
            'signal_id',
            'source',
            'text',
            'text_extra',
            'status',
            'location',
            'category',
            'reporter',
            'priority',
            'created_at',
            'updated_at',
            'incident_date_start',
            'incident_date_end',
            'operational_date',
            'extra_properties',
            'notes_count',
            'parent_id',
            'child_ids',
        )
        read_only_fields = (
            'id',
            'signal_id',
            'created_at',
            'updated_at',
        )

    def get_child_ids(self, obj):
        return obj.children.values_list('id', flat=True)


class SignalAuthHALSerializerDetail(HALSerializer):
    """Read-only serializer for single `Signal` object."""
    _display = DisplayField()
    id = serializers.IntegerField(label='ID', read_only=True)
    signal_id = serializers.CharField(label='SIGNAL_ID', read_only=True)
    location = _NestedLocationModelSerializer(read_only=True)
    reporter = _NestedReporterModelSerializer(read_only=True)
    status = _NestedStatusModelSerializer(read_only=True)
    category = _NestedCategoryModelSerializer(source='category_assignment', read_only=True)
    priority = _NestedPriorityModelSerializer(read_only=True)
    image = serializers.ImageField(source='image_crop', read_only=True)
    notes_count = serializers.SerializerMethodField()

    parent_id = serializers.IntegerField(read_only=True)
    child_ids = serializers.SerializerMethodField(read_only=True)

    serializer_url_field = SignalLinksField

    def get_notes_count(self, obj):
        return obj.notes.count()

    class Meta(object):
        model = Signal
        fields = (
            '_links',
            '_display',
            'id',
            'signal_id',
            'source',
            'text',
            'text_extra',
            'status',
            'location',
            'category',
            'reporter',
            'priority',
            'created_at',
            'updated_at',
            'incident_date_start',
            'incident_date_end',
            'operational_date',
            'image',
            'extra_properties',
            'notes_count',
            'parent_id',
            'child_ids',
        )
        read_only_fields = (
            'id',
            'signal_id',
            'created_at',
            'updated_at',
        )

    def get_child_ids(self, obj):
        return obj.children.values_list('id', flat=True)


class LocationHALSerializer(AddExtrasMixin, NearAmsterdamValidatorMixin, HALSerializer):
    _signal = serializers.PrimaryKeyRelatedField(queryset=Signal.objects.all())

    class Meta:
        model = Location
        fields = (
            'id',
            '_signal',
            'stadsdeel',
            'buurt_code',
            'address',
            'geometrie',
            'created_by',
            'extra_properties',
            'created_at',
            'bag_validated',
        )

    def create(self, validated_data):
        validated_data = self.add_user(validated_data)
        validated_data['created_by'] = validated_data.pop('user')

        signal = validated_data.pop('_signal')
        location = Signal.actions.update_location(validated_data, signal)
        return location


class StatusHALSerializer(AddExtrasMixin, HALSerializer):
    _display = DisplayField()
    _signal = serializers.PrimaryKeyRelatedField(queryset=Signal.objects.all())
    serializer_url_field = StatusLinksField
    state_display = serializers.CharField(source='get_state_display', read_only=True)

    class Meta(object):
        model = Status
        fields = (
            '_links',
            '_display',
            '_signal',
            'text',
            'user',
            'target_api',
            'state',
            'state_display',
            'extra_properties',
            'created_at',
        )
        extra_kwargs = {
            'state': {'choices': workflow.STATUS_CHOICES_API}
        }

    def create(self, validated_data):
        validated_data = self.add_user(validated_data)

        signal = validated_data.pop('_signal')
        status = Signal.actions.update_status(validated_data, signal)
        return status

    def validate(self, data):
        is_status_change_to_sigmax = (data['state'] == workflow.TE_VERZENDEN and
                                      data.get('target_api', None) == Status.TARGET_API_SIGMAX)
        if is_status_change_to_sigmax:
            request = self.context.get('request', None)
            if request and not request.user.has_perm('signals.push_to_sigmax'):
                raise PermissionDenied({
                    'state': "You don't have permissions to push to Sigmax/CityControl."
                })

        try:
            status = Status(**data)
            status.clean()
        except ValidationError as e:
            raise serializers.ValidationError(e.error_dict)

        return data


class CategoryHALSerializer(AddExtrasMixin, HALSerializer):
    serializer_url_field = CategoryLinksField
    _display = DisplayField()

    _signal = serializers.PrimaryKeyRelatedField(queryset=Signal.objects.all())

    # Should be required, but to make it work with the backwards compatibility fix it's not required
    # at the moment..
    sub_category = LegacyCategoryHyperlinkedRelatedField(write_only=True, required=False,
                                                         source='category')

    sub = serializers.CharField(source='category.name', read_only=True)
    sub_slug = serializers.CharField(source='category.slug', read_only=True)
    main = serializers.CharField(source='category.parent.name', read_only=True)
    main_slug = serializers.CharField(source='category.parent.slug', read_only=True)

    # Backwards compatibility fix for departments, should be retrieved from category terms resource.
    department = serializers.SerializerMethodField(source='category.departments',
                                                   read_only=True)

    class Meta(object):
        model = CategoryAssignment
        fields = (
            '_links',
            '_display',
            '_signal',
            'sub_category',
            'sub',
            'sub_slug',
            'main',
            'main_slug',
            'department',
            'created_by',
            'created_at',
        )

    def get_department(self, obj):
        return ', '.join(obj.category.departments.values_list('code', flat=True))

    def to_internal_value(self, data):
        internal_data = super().to_internal_value(data)

        if 'sub_category' in data:
            # Fix for renaming sub_category to category internally
            data['category'] = data['sub_category']
            del data['sub_category']

        # Backwards compatibility fix to let this endpoint work with `sub` as key.
        is_main_name_posted = 'main' in data
        is_sub_name_posted = 'sub' in data
        is_category_not_posted = 'category' not in data
        if is_main_name_posted and is_sub_name_posted and is_category_not_posted:
            try:
                category = Category.objects.get(parent__name__iexact=data['main'],
                                                name__iexact=data['sub'])
            except Category.DoesNotExist:
                internal_data['category'] = Category.objects.get(id=76)  # Overig
            else:
                internal_data['category'] = category

        return internal_data

    def validate(self, attrs):
        if 'category' in attrs:
            if attrs['_signal'].category_assignment.category.id == attrs['category'].id:
                raise ValidationError('Cannot assign the same category twice')

        return super(CategoryHALSerializer, self).validate(attrs=attrs)

    def create(self, validated_data):
        validated_data = self.add_user(validated_data)
        validated_data['created_by'] = validated_data.pop('user')

        signal = validated_data.pop('_signal')
        category = Signal.actions.update_category_assignment(validated_data, signal)
        return category


class PriorityHALSerializer(AddExtrasMixin, HALSerializer):
    _display = DisplayField()
    _signal = serializers.PrimaryKeyRelatedField(queryset=Signal.objects.all())
    serializer_url_field = PriorityLinksField

    class Meta:
        model = Priority
        fields = (
            '_links',
            '_display',
            'id',
            '_signal',
            'priority',
            'created_at',
            'created_by',
        )

    def create(self, validated_data):
        validated_data = self.add_user(validated_data)
        validated_data['created_by'] = validated_data.pop('user')

        signal = validated_data.pop('_signal')
        priority = Signal.actions.update_priority(validated_data, signal)
        return priority


#
# Category terms
#

class _NestedDepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = (
            'code',
            'name',
            'is_intern',
        )


#
# Note objects field
#

class NoteHALSerializer(AddExtrasMixin, HALSerializer):
    _signal = serializers.PrimaryKeyRelatedField(queryset=Signal.objects.all())
    serializer_url_field = NoteHyperlinkedIdentityField

    class Meta:
        model = Note
        fields = (
            '_links',
            'text',
            'created_at',
            'created_by',
            '_signal',
        )

    def create(self, validated_data):
        validated_data = self.add_user(validated_data)
        validated_data['created_by'] = validated_data.pop('user')

        signal = validated_data.pop('_signal')
        note = Signal.actions.create_note(validated_data, signal)
        return note
