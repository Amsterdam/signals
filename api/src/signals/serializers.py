# import json
# import logging

from rest_framework import serializers

from datapunt_api.rest import DisplayField
from datapunt_api.rest import HALSerializer
from datapunt_api.rest import RelatedSummaryField

from signals.models import Signal
from signals.models import Reporter
from signals.models import Category
from signals.models import Status
from signals.models import Location


class LocationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Location
        fields = '__all__'


class SignalPublicSerializer(HALSerializer):
    _display = DisplayField()

    location = LocationSerializer()

    class Meta(object):
        model = Signal
        fields = [
            "_links",
            "_display",
            # "pk",
            "signal_id",
            "text",
            "text_extra",
            "status",
            "location",
            "category",
            # DO NOT ENABLE
            # make test for this
            # "reporter",
            "created_at",
            "updated_at",
            "incident_date_start",
            "incident_date_end",
            "operational_date",
            "image",
            "upload",
        ]


class StatusSerializer(HALSerializer):
    _display = DisplayField()

    # signal = SignalSerializer()

    class Meta(object):
        model = Status
        fields = [
            "_links",
            "_display",
            # "id",
            # "signal",
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
