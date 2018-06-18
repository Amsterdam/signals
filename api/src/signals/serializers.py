# import json
# import logging

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


class LocationModelSerializer(GeoFeatureModelSerializer):

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
        fields = '__all__'


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


class ReporterModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = Reporter
        fields = '__all__'


class CategoryModelSerializer(serializers.ModelSerializer):

    class Meta(object):
        model = Category
        fields = [
            # "id",
            "main",
            "sub",
        ]


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


class SignalAuthSerializer(HALSerializer):
    _display = DisplayField()
    id = IntegerField(label='ID', read_only=True)
    signal_id = CharField(label='SIGNAL_ID', read_only=True)
    location = LocationModelSerializer()
    reporter = ReporterModelSerializer()
    status = StatusModelSerializer()
    category = CategoryModelSerializer()

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

        location = Location.objects.create(**location)
        category = Category.objects.create(**category)
        status = Status.objects.create(**status)
        reporter = Reporter.objects.create(**reporter)

        location.signal.add(signal)
        status.signal.add(signal)
        category.signal.add(signal)
        reporter.signal.add(signal)

        status.save()
        reporter.save()
        category.save()
        location.save()

        return signal

    def update(self, instance, validated_data):
        pass


class StatusSerializer(HALSerializer):
    _display = DisplayField()

    signal = SignalPublicSerializer()

    class Meta(object):
        model = Status
        fields = [
            "_links",
            "_display",
            "id",
            "signal",
            "text",
            "user",
            "extern",
            "state",
            "created_at",
            "updated_at",
            "extra_properties",
        ]



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
