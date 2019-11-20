from signals.apps.api.generics.serializers import SIAModelSerializer
from signals.apps.signals.models import Reporter


class _NestedReporterModelSerializer(SIAModelSerializer):
    class Meta:
        model = Reporter
        fields = (
            'email',
            'phone',
        )
