import logging
from collections import OrderedDict
from datetime import timedelta, timezone

from datapunt_api.rest import DisplayField
from datapunt_api.rest import HALSerializer
from django.core.exceptions import ValidationError
from django.db import transaction, connection
from django.forms import ImageField
from django.utils.datetime_safe import datetime
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.serializers import CharField
from rest_framework.serializers import IntegerField, ModelSerializer
from rest_framework.throttling import BaseThrottle

from signals.messaging.categories import get_departments
from signals.messaging.send_emails import (
    handle_status_change, handle_create_signal)
from signals.models import Category
from signals.models import Location
from signals.models import Reporter
from signals.models import Signal, STATUS_OVERGANGEN, AFGEHANDELD
from signals.models import Status


log = logging.getLogger(__name__)


class LocationModelSerializer(serializers.ModelSerializer):
    id = IntegerField(label='ID', read_only=True)

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


class LocationSerializer(HALSerializer):
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
        # django rest does default the good thing
        location = Location(**validated_data)
        location.save()
        # update status on signal
        signal = Signal.objects.get(id=location._signal_id)
        signal.location = location
        signal.save()
        return location

    def update(self, instance, validated_data):
        """Should not be implemented.
        """
        pass


class StatusModelSerializer(serializers.ModelSerializer):
    id = IntegerField(label='ID', read_only=True)

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

        extra_kwargs = {'_signal': {'required': False}}


class StatusUnauthenticatedModelSerializer(serializers.ModelSerializer):
    id = IntegerField(label='ID', read_only=True)

    class Meta:
        model = Status
        fields = (
            'id',
            'state',
        )

        extra_kwargs = {'_signal': {'required': False}}


class ReporterModelSerializer(serializers.ModelSerializer):
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


class CategoryModelSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = Category
        fields = [
            "main",
            "sub",
            "department",
            "priority",
        ]

        extra_kwargs = {'_signal': {'required': False}}


class SignalUpdateImageSerializer(ModelSerializer):
    id = IntegerField(label='ID', read_only=True)
    signal_id = CharField(label='SIGNAL_ID')

    class Meta(object):
        model = Signal
        fields = [
            'id',
            'signal_id',
            'image'
        ]

    def create(self, validated_data):
        """
        This serializer is only used for updating
        """
        signal_id = validated_data.get('signal_id')
        instance = Signal.objects.get(signal_id=signal_id)
        return self.update(instance, validated_data)

    def validate(self, attrs):
        # self.data.is_valid()
        image = self.initial_data.get('image', False)
        if image:
            if image.size > 8388608:  # 3MB = 8*1024*1024
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


class SignalCreateSerializer(ModelSerializer):
    id = IntegerField(label='ID', read_only=True)
    signal_id = CharField(label='SIGNAL_ID', read_only=True)
    location = LocationModelSerializer()
    reporter = ReporterModelSerializer()
    status = StatusModelSerializer()
    category = CategoryModelSerializer()

    # Explicitly specify fields with auto_now_add=True
    # to show in the rest framework
    created_at = serializers.DateTimeField()
    incident_date_start = serializers.DateTimeField()

    class Meta(object):
        model = Signal
        fields = [
            # "pk",
            "id",
            "signal_id",
            "source",
            "text",
            "text_extra",
            "status",
            "location",
            "category",
            "reporter",
            "created_at",
            "updated_at",
            "incident_date_start",
            "incident_date_end",
            "operational_date",
            "image",
            "extra_properties",
            # "upload",   For now we only upload one image
        ]

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

    def validate(self, data):
        # The status can only be 'm' when created
        if data['status']['state'] not in STATUS_OVERGANGEN['']:
            raise serializers.ValidationError(
                f"Invalid status: {data['status']['state']}")

        image = self.initial_data.get('image', False)
        if image:
            if image.size > 3145728:  # 3MB = 3*1024*1024
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
            if departments and ('department' not in data['category'] or not data['category']['department']):
                data['category']['department'] = departments
            elif not departments:
                log.warning(f"Department not found for subcategory : {data['category']['sub']}")
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


class SignalLinksField(serializers.HyperlinkedIdentityField):
    """
    Return authorized url. handy for development.
    """

    def to_representation(self, value):
        request = self.context.get('request')

        result = OrderedDict([
            ('self', dict(
                href=self.get_url(value, "signal-auth-detail", request, None))
             ),
        ])

        return result


class SignalUnauthenticatedLinksField(serializers.HyperlinkedIdentityField):
    """
    Return url based on UUID instead of normal database id
    """
    lookup_field = 'signal_id'


class SignalUnauthenticatedSerializer(HALSerializer):
    _display = DisplayField()
    signal_id = CharField(label='SIGNAL_ID', read_only=True)
    status = StatusUnauthenticatedModelSerializer(read_only=True)

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


class SignalAuthSerializer(HALSerializer):
    _display = DisplayField()
    id = IntegerField(label='ID', read_only=True)
    signal_id = CharField(label='SIGNAL_ID', read_only=True)
    location = LocationModelSerializer(read_only=True)
    reporter = ReporterModelSerializer(read_only=True)
    status = StatusModelSerializer(read_only=True)
    category = CategoryModelSerializer(read_only=True)

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


class StatusLinksField(serializers.HyperlinkedIdentityField):
    """
    Return authorized url. handy for development.
    """

    def to_representation(self, value):
        request = self.context.get('request')

        result = OrderedDict([
            ('self', dict(
                href=self.get_url(value, "status-auth-detail", request, None))
             ),
        ])

        return result


class StatusSerializer(HALSerializer):
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
        """
        """

        with transaction.atomic():
            # django rest does default the good thing
            status = Status(**validated_data)
            status.save()
            # update status on signal
            signal = Signal.objects.get(id=status._signal_id)
            previous_status = signal.status
            signal.status = status
            signal.save()

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


class CategoryLinksField(serializers.HyperlinkedIdentityField):
    """
    Return authorized url. handy for development.
    """

    def to_representation(self, value):
        request = self.context.get('request')

        result = OrderedDict([
            ('self', dict(
                href=self.get_url(value, "category-auth-detail", request, None))
             ),
        ])

        return result


class CategorySerializer(HALSerializer):
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
                log.warning(f"Department not found for subcategory : {data['sub']}")
        else:
            raise serializers.ValidationError(
                f"Invalid category : missing sub")

        # TODO add validation
        return data


class ReporterLinksField(serializers.HyperlinkedIdentityField):
    """
    Return authorized url. handy for development.
    """

    def to_representation(self, value):
        request = self.context.get('request')

        result = OrderedDict([
            ('self', dict(
                href=self.get_url(value, "reporter-auth-detail", request, None))
             ),
        ])

        return result


class ReporterSerializer(HALSerializer):
    _display = DisplayField()
    serializer_url_field = ReporterLinksField

    # signal = RelatedSummaryField()

    class Meta(object):
        model = Reporter
        fields = [
            "_links",
            "_display",
            "id",
            "email",
            "phone",
            "created_at",
            "remove_at",
        ]
