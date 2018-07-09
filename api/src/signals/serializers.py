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

from signals.messaging.send_emails import handle_status_change, \
    handle_create_signal
from signals.models import Category
from signals.models import Location
from signals.models import Reporter
from signals.models import STATUS_OVERGANGEN
from rest_framework.throttling import BaseThrottle
from signals.models import Signal
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
        instance = Signal.objects.get(pk=signal_id)
        return self.update(instance, validated_data)

    def validate(self, attrs):
        # self.data.is_valid()
        image = self.initial_data.get('image', False)
        if image:
            if image._size > 3145728:  # 3MB = 3*1024*1024
                raise ValidationError("Foto mag maximaal 3Mb groot zijn.")
        else:
            raise ValidationError("Foto is een verplicht veld.")

        return attrs

    def update(self, instance, validated_data):
        image = validated_data['image']

        ## Only allow adding a photo if none is set.
        if instance.image is not None:
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
            # "upload",   For now we only upload one image
        ]

    def create(self, validated_data):
        status_data = validated_data.pop('status')
        location_data = validated_data.pop('location')
        reporter_data = validated_data.pop('reporter')
        if 'remove_at' not in reporter_data or reporter_data[
            'remove_at'] is None:
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
        pass

    def validate(self, data):
        # The status can only be 'm' when created
        if data['status']['state'] not in STATUS_OVERGANGEN['']:
            raise serializers.ValidationError(
                f"Invalid status: {data['status']['state']}")

        image = self.initial_data.get('image', False)
        if image:
            if image._size > 3145728:  # 3MB = 3*1024*1024
                raise ValidationError("Foto mag maximaal 3Mb groot zijn.")

        # TODO add further validation
        return data


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

    user = serializers.SerializerMethodField()

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

    def update(self, instance, validated_data):
        """Should not be implemented.
        """
        pass

    def get_user(self, obj):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "get_token_subject"):
            user = request.get_token_subject
        if user is None:
            raise serializers.ValidationError("Missing user in request")
        if user.find('@') == -1:
            log.warning(f"User without e-mail : {user}")
            user += '@unknown.nl'
        return user

    def validate(self, data):
        # Get current status for signal
        signal = data['_signal']
        if data['state'] not in STATUS_OVERGANGEN[signal.status.state]:
            raise serializers.ValidationError(
                f"Invalid state transition from {signal.status.state} "
                f"to {data['state']}")
        ip = self.add_ip(data)
        if ip is not None:
            extra_properties = data['extra_properties']
            if extra_properties is None:
                extra_properties = {}
            extra_properties['IP'] = ip
            data['extra_properties'] = extra_properties
        # TODO add further validation
        return data

    def add_ip(self, data):
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

    def update(self, instance, validated_data):
        """
        Should not be implemented.
        """
        pass

    # def validate(self, data):
    #     # TODO add validation
    #     return data


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
