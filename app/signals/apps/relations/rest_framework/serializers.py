from rest_framework import serializers

from signals.apps.signals.models import Signal


class RelatedSignalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Signal
        fields = [
            'id',
        ]
