from rest_framework.serializers import ModelSerializer

from signals.apps.reporting.models import ReportIndicator


class _NestedReportIndicatorSerializer(ModelSerializer):
    class Meta:
        model = ReportIndicator
        read_only_fields = ('code',)
