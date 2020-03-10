from signals.apps.api.generics.serializers import SIAModelSerializer
from signals.apps.signals.models import Type


class _NestedTypeModelSerializer(SIAModelSerializer):
    class Meta:
        model = Type
        fields = (
            'name',
        )
