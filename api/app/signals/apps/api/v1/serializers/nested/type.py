from rest_framework import serializers

from signals.apps.api.generics.serializers import SIAModelSerializer
from signals.apps.signals.models import Type


class _NestedTypeModelSerializer(SIAModelSerializer):
    code = serializers.CharField(source='name', max_length=3)

    class Meta:
        model = Type
        fields = (
            'code',
            'created_at',
            'created_by'
        )
