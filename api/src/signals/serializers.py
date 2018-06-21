# import json
# import logging
from collections import OrderedDict

from django.db import transaction, connection

from rest_framework import serializers
from rest_framework.serializers import IntegerField, ModelSerializer
from rest_framework.serializers import CharField

from datapunt_api.rest import DisplayField
from datapunt_api.rest import HALSerializer

from signals.models import Signal
from signals.models import Reporter
from signals.models import Category
from signals.models import Status
from signals.models import Location


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
        """
        """
        # django rest does default the good thing
        location = Location(**validated_data)
        location.save()
        # update status on signal
        location.signal.add(location._signal)
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
            '_signal',
            'extern',
            'extra_properties',
        )

        extra_kwargs = {'_signal': {'required': False}}


class ReporterModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = Reporter
        fields = '__all__'

        extra_kwargs = {'_signal': {'required': False}}


class CategoryModelSerializer(serializers.ModelSerializer):

    class Meta(object):
        model = Category
        fields = [
            # "id",
            "main",
            "sub",
            "priority",
        ]

        extra_kwargs = {'_signal': {'required': False}}


# class SignalPublicSerializer(HALSerializer):
#     """
#     Public version of Signals
#     """
#     _display = DisplayField()
#
#     location = LocationModelSerializer()
#
#     class Meta(object):
#         model = Signal
#         fields = [
#             "_links",
#             "_display",
#             # "pk",
#             "signal_id",
#             # "text",
#             # "text_extra",
#             # "status",
#             "location",
#             # "category",
#             # DO NOT ENABLE
#             # make test for this
#             # "reporter",
#             "created_at",
#             # "updated_at",
#             # "incident_date_start",
#             # "incident_date_end",
#             # "operational_date",
#             # "image",
#             # "upload",
#         ]


class SignalCreateSerializer(ModelSerializer):
    id = IntegerField(label='ID', read_only=True)
    signal_id = CharField(label='SIGNAL_ID', read_only=True)
    location = LocationModelSerializer()
    reporter = ReporterModelSerializer()
    status = StatusModelSerializer()
    category = CategoryModelSerializer()

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
        category_data = validated_data.pop('category')

        with transaction.atomic():
            cursor = connection.cursor()
            cursor.execute("select nextval('signals_signal_id_seq')")
            (signal_id,) = cursor.fetchone()
            location = Location.objects.create(_signal_id=signal_id, **location_data)
            category = Category.objects.create(_signal_id=signal_id, **category_data)
            status = Status.objects.create(_signal_id=signal_id, **status_data)
            reporter = Reporter.objects.create(_signal_id=signal_id, **reporter_data)
            signal = Signal.objects.create(id=signal_id, location=location, category=category, reporter=reporter,
                                           status=status, **validated_data)
        return signal

    def update(self, instance, validated_data):
        pass

    def validate(self, data):
        # TODO add validation
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
    location = LocationModelSerializer()
    reporter = ReporterModelSerializer()
    status = StatusModelSerializer()
    category = CategoryModelSerializer()

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
            "upload",
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
    _signal = serializers.PrimaryKeyRelatedField(queryset=Signal.objects.all())
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
        extra_kwargs = {'_signal': {'required': False}}

    def create(self, validated_data):
        """
        """
        # django rest does NOT default the good thing
        # validated_data['_signal_id'] = validated_data.pop('_signal')
        status = Status(**validated_data)
        status.save()
        # update status on signal
        status.signal.add(status._signal)
        return status

    def update(self, instance, validated_data):
        """Should not be implemented.
        """
        pass

    # def validate(self, data):
    #     # TODO add validation
    #     return data


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
    _signal = serializers.PrimaryKeyRelatedField(queryset=Signal.objects.all())
    serializer_url_field = CategoryLinksField

    class Meta(object):
        model = Category
        fields = [
            "_links",
            "_display",
            "id",
            "main",
            "sub",
            "priority",
            "_signal",
        ]

    def create(self, validated_data):
        """
        """
        # django rest does default the good thing
        category = Category(**validated_data)
        category.save()
        # update status on signal
        category.signal.add(category._signal)
        return category

    def update(self, instance, validated_data):
        """Should not be implemented.
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
