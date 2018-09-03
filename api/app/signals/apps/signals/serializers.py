import logging
from datetime import timedelta, timezone

from datapunt_api.rest import DisplayField, HALSerializer
from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.forms import ImageField
from django.utils.datetime_safe import datetime
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.throttling import BaseThrottle

from signals.apps.signals.models import (
    AFGEHANDELD,
    STATUS_OVERGANGEN,
    Category,
    Location,
    Reporter,
    Signal,
    Status
)
from signals.apps.signals.fields import (
    SignalLinksField,
    SignalUnauthenticatedLinksField,
    StatusLinksField,
    CategoryLinksField,
    ReporterLinksField
)
from signals.apps.signals.validators import NearAmsterdamValidatorMixin
from signals.messaging.send_emails import (
    handle_create_signal,
    handle_status_change
)
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
            '_signal': {'required': False},  # TODO is this needed?
        }


class _NestedCategoryModelSerializer(serializers.ModelSerializer):

    class Meta(object):
        model = Category
        fields = (
            'main',
            'sub',
            'department',
            'priority',
        )
        extra_kwargs = {
            '_signal': {'required': False},  # TODO is this needed?
        }


class _NestedReporterModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = Reporter
        fields = (
            'email',
            'phone',
            'remove_at',
            'created_at',
            'updated_at',
            'extra_properties',
        )

#
# Unauth serializers
#

class SignalCreateSerializer(serializers.ModelSerializer):
    location = _NestedLocationModelSerializer()
    reporter = _NestedReporterModelSerializer()
    status = _NestedStatusModelSerializer()
    category = _NestedCategoryModelSerializer()

    # Explicitly specify fields with auto_now_add=True
    # to show in the rest framework
    created_at = serializers.DateTimeField()
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
        )
        extra_kwargs = {
            'id': {'label': 'ID'},
            'signal_id': {'label': 'SIGNAL_ID'},
        }

    def create(self, validated_data):
        status_data = validated_data.pop('status')
        location_data = validated_data.pop('location')
        reporter_data = validated_data.pop('reporter')
        if 'remove_at' not in reporter_data or reporter_data['remove_at'] is None:
            remove_at = datetime.now(timezone.utc) + timedelta(weeks=2)
            reporter_data["remove_at"] = remove_at.isoformat()
        category_data = validated_data.pop('category')

        with transaction.atomic():
            cursor = connection.cursor()
            cursor.execute("select nextval('signals_signal_id_seq')")
            (signal_id,) = cursor.fetchone()
            location = Location.objects.create(_signal_id=signal_id,
                                               **location_data)
            category = Category.objects.create(_signal_id=signal_id,
                                               **category_data)

            status = Status.objects.create(_signal_id=signal_id, **status_data)
            reporter = Reporter.objects.create(_signal_id=signal_id,
                                               **reporter_data)
            signal = Signal.objects.create(id=signal_id, location=location,
                                           category=category, reporter=reporter,
                                           status=status, **validated_data)

        handle_create_signal(signal)
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
        fields = [
            "_links",
            "_display",
            "signal_id",
            "status",
            "created_at",
            "updated_at",
            "incident_date_start",
            "incident_date_end",
            "operational_date",
        ]


#
# Auth serializers
#

class SignalAuthSerializer(HALSerializer):
    _display = DisplayField()
    id = serializers.IntegerField(label='ID', read_only=True)
    signal_id = serializers.CharField(label='SIGNAL_ID', read_only=True)
    location = _NestedLocationModelSerializer(read_only=True)
    reporter = _NestedReporterModelSerializer(read_only=True)
    status = _NestedStatusModelSerializer(read_only=True)
    category = _NestedCategoryModelSerializer(read_only=True)

    image = ImageField(max_length=50, allow_empty_file=False)

    serializer_url_field = SignalLinksField

    class Meta(object):
        model = Signal
        fields = [
            "_links",
            "_display",
            # "pk",
            "id",
            "signal_id",
            "source",
            "text",
            "text_extra",
            "status",
            "location",
            "category",
            # DO NOT ENABLE
            # make test for this
            "reporter",
            "created_at",
            "updated_at",
            "incident_date_start",
            "incident_date_end",
            "operational_date",
            "image",
            "extra_properties",
            # "upload",
        ]

    def update(self, instance, validated_data):
        pass


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
        signal = validated_data.pop('signal')
        location = Signal.actions.update_location(**validated_data, signal)
        return location

    def update(self, instance, validated_data):
        raise NotImplementedError('`update()` is not allowed with this serializer.')


class StatusHALSerializer(HALSerializer):
    _display = DisplayField()
    _signal = serializers.PrimaryKeyRelatedField(
        queryset=Signal.objects.all().order_by("id"))
    serializer_url_field = StatusLinksField

    class Meta(object):
        model = Status
        fields = [
            "_links",
            "_display",
            "id",
            "text",
            "user",
            "extern",
            "_signal",
            "state",
            "created_at",
            "updated_at",
            "extra_properties",
        ]
        # extra_kwargs = {'_signal': {'required': False}}

    def create(self, validated_data):
        with transaction.atomic():
            signal = validated_data['signal']
            status = Signal.actions.update_status(**validated_data, signal)

        # TODO fix previous state (move it to Django signals)
        if status:
            handle_status_change(signal, previous_status)
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
    _display = DisplayField()
    _signal = serializers.PrimaryKeyRelatedField(
        queryset=Signal.objects.all().order_by("id"))
    serializer_url_field = CategoryLinksField

    class Meta(object):
        model = Category
        fields = [
            "_links",
            "_display",
            "id",
            "main",
            "sub",
            "department",
            "priority",
            "_signal",
        ]

    def create(self, validated_data):
        with transaction.atomic():
            # django rest does default the good thing
            category = Category(**validated_data)
            category.save()
            # update status on signal
            signal = Signal.objects.get(id=category._signal_id)
            signal.category = category
            signal.save()
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
