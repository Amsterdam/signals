# import json
# import logging
from collections import OrderedDict

from rest_framework import serializers
from rest_framework.serializers import IntegerField
from rest_framework.serializers import CharField

from rest_framework_gis.serializers import GeometrySerializerMethodField
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from datapunt_api.rest import DisplayField
from datapunt_api.rest import HALSerializer
from datapunt_api.rest import RelatedSummaryField

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
        ]

        extra_kwargs = {'_signal': {'required': False}}


class SignalPublicSerializer(HALSerializer):
    """
    Public version of Signals
    """
    _display = DisplayField()

    location = LocationModelSerializer()

    class Meta(object):
        model = Signal
        fields = [
            "_links",
            "_display",
            # "pk",
            "signal_id",
            # "text",
            # "text_extra",
            # "status",
            "location",
            # "category",
            # DO NOT ENABLE
            # make test for this
            # "reporter",
            "created_at",
            # "updated_at",
            # "incident_date_start",
            # "incident_date_end",
            # "operational_date",
            # "image",
            # "upload",
        ]


class AuthLinksField(serializers.HyperlinkedIdentityField):
    """
    Return authorized url. handy for development.
    maybe also for Frontend.

    Needs discussion
    """

    def to_representation(self, value):
        request = self.context.get('request')

        result = OrderedDict([
            ('self', dict(
                href=self.get_url(value, self.view_name, request, None))
             ),
            ('self_auth', dict(
                href=self.get_url(value, 'signal-auth-detail', request, None))
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

    serializer_url_field = AuthLinksField

    class Meta(object):
        model = Signal
        fields = [
            "_links",
            "_display",
            # "pk",
            "id",
            "signal_id",
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

    def create(self, validated_data):
        signal = Signal.objects.create()
        signal.save()

        status = validated_data.pop('status')
        location = validated_data.pop('location')
        reporter = validated_data.pop('reporter')
        category = validated_data.pop('category')

        location = Location(_signal=signal, **location)
        category = Category(_signal=signal, **category)
        status = Status(_signal=signal, **status)
        reporter = Reporter(_signal=signal, **reporter)

        status.save()
        reporter.save()
        category.save()
        location.save()

        location.signal.add(signal)
        status.signal.add(signal)
        category.signal.add(signal)
        reporter.signal.add(signal)

        return signal

    def update(self, instance, validated_data):
        pass


class StatusSerializer(HALSerializer):
    _display = DisplayField()

    # signal = SignalPublicSerializer()

    class Meta(object):
        model = Status
        fields = [
            "_links",
            "_display",
            "id",
            # "signal",
            "_signal",
            "text",
            "user",
            "extern",
            "_signal",
            "state",
            "created_at",
            "updated_at",
            "extra_properties",
        ]
        extra_kwargs = {
            '_signals': {'required': False},
            '_signal': {'required': False},
        }

    def create(self, validated_data):
        """
        """
        # django rest does default the good thing
        status = Status(**validated_data)
        status.save()
        # update status on signal
        status.signal.add(status._signal)
        return status

    def update(self, instance, validated_data):
        """Should not be implemented.
        """
        pass


class CategorySerializer(HALSerializer):
    _display = DisplayField()

    signal = RelatedSummaryField()

    class Meta(object):
        model = Category
        fields = [
            "_links",
            "_display",
            # "id",
            "main",
            "sub",
            "signal",
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


class ReporterSerializer(HALSerializer):
    _display = DisplayField()

    # signal = RelatedSummaryField()

    class Meta(object):
        model = Reporter
        fields = [
            "_links",
            "_display",
            "id",
            "email",
            "phone",
            "created_at"
            "remove_at"
        ]

        # extra_kwargs = {'_signal': {'required': False}}
        # validators = []
