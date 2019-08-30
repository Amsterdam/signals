from collections import OrderedDict

from datapunt_api.rest import HALSerializer
from rest_framework import serializers

from signals.apps.reporting.models import ReportDefinition
# from signals.apps.reporting.serializers.report_indicator import _NestedReportIndicatorSerializer


class PrivateReportLinkField(serializers.HyperlinkedIdentityField):
    def to_representation(self, value):
        request = self.context.get('request')

        result = OrderedDict([
            ('self', dict(href=self.get_url(value, "private-reports-detail", request, None))),
        ])

        return result


class PrivateReportSerializer(HALSerializer):
    serializer_url_field = PrivateReportLinkField

    class Meta:
        model = ReportDefinition
        fields = (
            '_links',
            'name',
            'description',
            'interval',
            'category',
            'area',
        )
        read_only = (
            'name',
            'description',
            'interval',
            'category',
            'area',
        )
