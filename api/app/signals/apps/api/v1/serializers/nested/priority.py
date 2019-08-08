from rest_framework import serializers

from signals.apps.signals.models import Priority


class _NestedPriorityModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Priority
        fields = (
            'priority',
            'created_by',
        )
        read_only_fields = (
            'created_by',
        )
