from rest_framework import serializers

from signals.apps.signals.models import Reporter


class _NestedReporterModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reporter
        fields = (
            'email',
            'phone',
        )
