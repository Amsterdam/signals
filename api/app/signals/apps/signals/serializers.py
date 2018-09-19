import logging

from datapunt_api.rest import DisplayField, HALSerializer
from django.core.exceptions import ValidationError
from django.forms import ImageField
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.throttling import BaseThrottle

from signals.apps.signals.fields import (
    CategoryLinksField,
    PriorityLinksField,
    SignalLinksField,
    SignalUnauthenticatedLinksField,
    StatusLinksField
)
from signals.apps.signals.models import (
    AFGEHANDELD,
    STATUS_OVERGANGEN,
    CategoryAssignment,
    Location,
    Priority,
    Reporter,
    Signal,
    Status,
    SubCategory
)
from signals.apps.signals.validators import NearAmsterdamValidatorMixin
from signals.settings.categories import get_departments

logger = logging.getLogger(__name__)


class SignalUpdateImageSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(label='ID', read_only=True)
    signal_id = serializers.CharField(label='SIGNAL_ID')

    class Meta(object):
        model = Signal
        fields = (
            'id',
            'signal_id',
            'image'
        )

    def create(self, validated_data):
        signal_id = validated_data.get('signal_id')
        instance = Signal.objects.get(signal_id=signal_id)
        return self.update(instance, validated_data)

    def validate(self, attrs):
        # self.data.is_valid()
        image = self.initial_data.get('image', False)
        if image:
            if image.size > 8388608:  # 8MB = 8*1024*1024
                raise ValidationError("Foto mag maximaal 8Mb groot zijn.")
        else:
            raise ValidationError("Foto is een verplicht veld.")

        return attrs

    def update(self, instance, validated_data):
        image = validated_data['image']

        # Only allow adding a photo if none is set.
        if instance.image:
            raise PermissionDenied("Melding is reeds van foto voorzien.")

        if image:
            setattr(instance, 'image', image)
            instance.save()

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
        )
        read_only_fields = (
            'id',
        )
        extra_kwargs = {
            'id': {'label': 'ID', },
        }


class _NestedStatusModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = Status
        fields = (
            'id',
            'text',
            'user',
            'target_api',
            'state',
            'extern',
            'extra_properties',
        )
        read_only_fields = (
            'id',
        )
        extra_kwargs = {
            'id': {'label': 'ID'},
        }


class _NestedCategoryModelSerializer(serializers.ModelSerializer):
    sub = serializers.CharField(source='sub_category.name', read_only=True)
    sub_code = serializers.CharField(source='sub_category.code', read_only=True)
    main = serializers.CharField(source='sub_category.main_category.name', read_only=True)

    # Should be required, but to make it work with the backwards compatibility fix it's not required
    # at the moment..
    sub_category = serializers.PrimaryKeyRelatedField(
        queryset=SubCategory.objects.all(),
        write_only=True,
        required=False)

    class Meta:
        model = CategoryAssignment
        fields = (
            'sub',
            'sub_code',
            'main',
            'sub_category',
        )

    def to_internal_value(self, data):
        internal_data = super().to_internal_value(data)

        # Backwards compatibility fix to let this endpoint work with `sub` as key.
        if 'sub' in data and 'sub_category' not in data:
            try:
                sub_category = SubCategory.objects.get(name=data['sub'])
            except SubCategory.DoesNotExist:
                pass
            else:
                internal_data['sub_category'] = sub_category

        return internal_data


class _NestedReporterModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = Reporter
        fields = (
            'email',
            'phone',
            'extra_properties',
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

    incident_date_start = serializers.DateTimeField()

    class Meta(object):
        model = Signal
        fields = (
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
        }

    def create(self, validated_data):
        status_data = validated_data.pop('status')
        location_data = validated_data.pop('location')
        reporter_data = validated_data.pop('reporter')
        category_assignment_data = validated_data.pop('category_assignment')
        signal = Signal.actions.create_initial(
            validated_data, location_data, status_data, category_assignment_data, reporter_data)
        return signal

    def update(self, instance, validated_data):
        raise NotImplementedError('`update()` is not allowed with this serializer.')

    def validate(self, data):  # noqa: C901
        # The status can only be 'm' when created
        if data['status']['state'] not in STATUS_OVERGANGEN['']:
            raise serializers.ValidationError(
                f"Invalid status: {data['status']['state']}")

        image = self.initial_data.get('image', False)
        if image:
            if image.size > 8388608:  # 8MB = 8*1024*1024
                raise ValidationError("Maximum photo size is 3Mb.")
        ip = self.add_ip()
        if ip is not None:
            if 'extra_properties' in data['status']:
                extra_properties = data['status']['extra_properties']
            else:
                extra_properties = {}
            extra_properties['IP'] = ip
            data['status']['extra_properties'] = extra_properties

        if 'category' in data and 'sub' in data['category']:
            if len(data['category']) < 1:
                raise serializers.ValidationError("Invalid category")

            departments = get_departments(data['category']['sub'])
            if departments and ('department' not in data['category'] or
                                not data['category']['department']):
                data['category']['department'] = departments
            elif not departments:
                logger.warning(f"Department not found for subcategory : {data['category']['sub']}")
        else:
            raise serializers.ValidationError(
                f"Invalid category : missing sub")

        request = self.context.get("request")
        if request.user and not request.user.is_anonymous:
            data['user'] = request.user.get_username()

        # TODO add further validation
        return data

    def add_ip(self):
        ip = None
        request = self.context.get("request")
        if request and hasattr(request, "get_token_subject"):
            ip = BaseThrottle.get_ident(None, request)
        return ip


class _NestedStatusUnauthenticatedModelSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(label='ID', read_only=True)

    class Meta:
        model = Status
        fields = (
            'id',
            'state',
        )
        extra_kwargs = {'_signal': {'required': False}}


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

class SignalAuthHALSerializer(HALSerializer):
    _display = DisplayField()
    id = serializers.IntegerField(label='ID', read_only=True)
    signal_id = serializers.CharField(label='SIGNAL_ID', read_only=True)
    location = _NestedLocationModelSerializer(read_only=True)
    reporter = _NestedReporterModelSerializer(read_only=True)
    status = _NestedStatusModelSerializer(read_only=True)
    category = _NestedCategoryModelSerializer(source='category_assignment', read_only=True)
    priority = _NestedPriorityModelSerializer(read_only=True)

    image = ImageField(max_length=50, allow_empty_file=False)

    serializer_url_field = SignalLinksField

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
        )
        read_only_fields = (
            'id',
            'signal_id',
            'created_at',
            'updated_at',
        )


class LocationHALSerializer(NearAmsterdamValidatorMixin, HALSerializer):
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
            'extra_properties',
        )

    def create(self, validated_data):
        signal = validated_data.pop('_signal')
        location = Signal.actions.update_location(validated_data, signal)
        return location

    def update(self, instance, validated_data):
        raise NotImplementedError('`update()` is not allowed with this serializer.')


class StatusHALSerializer(HALSerializer):
    _display = DisplayField()
    _signal = serializers.PrimaryKeyRelatedField(queryset=Signal.objects.all())
    serializer_url_field = StatusLinksField

    class Meta(object):
        model = Status
        fields = (
            '_links',
            '_display',
            'id',
            'text',
            'user',
            'extern',
            '_signal',
            'state',
            'extra_properties',
            'created_at',
        )

    def create(self, validated_data):
        signal = validated_data.pop('_signal')
        status = Signal.actions.update_status(validated_data, signal)
        return status

    def validate(self, data):
        # Get current status for signal
        signal = data['_signal']

        # Validating "state machine".
        if data['state'] not in STATUS_OVERGANGEN[signal.status.state]:
            raise serializers.ValidationError(
                f"Invalid state transition from {signal.status.state} "
                f"to {data['state']}")

        # Validating required field `text` when status is `AFGEHANDELD`.
        if data['state'] == AFGEHANDELD and not data['text']:
            raise serializers.ValidationError(
                {'text': 'This field is required.'})

        ip = self.add_ip()
        if ip is not None:
            if 'extra_properties' in data:
                extra_properties = data['extra_properties']
            else:
                extra_properties = {}
            extra_properties['IP'] = ip
            data['extra_properties'] = extra_properties

        request = self.context.get("request")
        if request.user and not request.user.is_anonymous:
            data['user'] = request.user.get_username()

        # TODO add further validation
        return data

    def add_ip(self):
        ip = None
        request = self.context.get("request")
        if request and hasattr(request, "get_token_subject"):
            ip = BaseThrottle.get_ident(None, request)
        return ip


class CategoryHALSerializer(HALSerializer):
    serializer_url_field = CategoryLinksField
    _display = DisplayField()

    _signal = serializers.PrimaryKeyRelatedField(queryset=Signal.objects.all())

    # Should be required, but to make it work with the backwards compatibility fix it's not required
    # at the moment..
    sub_category = serializers.PrimaryKeyRelatedField(
        queryset=SubCategory.objects.all(),
        write_only=True,
        required=False)

    sub = serializers.CharField(source='sub_category.name', read_only=True)
    sub_code = serializers.CharField(source='sub_category.code', read_only=True)
    main = serializers.CharField(source='sub_category.main_category.name', read_only=True)

    class Meta(object):
        model = CategoryAssignment
        fields = [
            '_links',
            '_display',
            '_signal',
            'sub',
            'sub_code',
            'main',
        ]

    def create(self, validated_data):
        signal = validated_data.pop('_signal')
        category = Signal.actions.update_category_assignment(validated_data, signal)
        return category

    def validate(self, data):
        if 'sub' in data:
            departments = get_departments(data['sub'])
            if departments and ('department' not in data or not data['department']):
                data['department'] = departments
            elif not departments:
                logger.warning(f"Department not found for subcategory : {data['sub']}")
        else:
            raise serializers.ValidationError(
                f"Invalid category : missing sub")

        # TODO add validation
        return data


class PriorityHALSerializer(HALSerializer):
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
        )

    def create(self, validated_data):
        signal = validated_data.pop('_signal')
        priority = Signal.actions.update_priority(validated_data, signal)
        return priority
