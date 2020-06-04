from signals.apps.api.generics.serializers import SIAModelSerializer
from signals.apps.signals.models import Reporter


class _NestedReporterModelSerializer(SIAModelSerializer):
    class Meta:
        model = Reporter
        fields = (
            'email',
            'phone',
            'sharing_allowed',
        )

    def to_representation(self, *args, **kwargs):
        """
        For backwards compatibility we replace null in email and phone fields with empty string.
        """
        serialized = super().to_representation(*args, **kwargs)

        for fieldname, representation in serialized.items():
            if fieldname in ['email', 'phone']:
                if representation is None:
                    serialized[fieldname] = ''
        return serialized

    def to_internal_value(self, data):
        """
        For backwards compatibility we replace empty string in email and phone fields with null.
        """
        if 'email' in data and data['email'] == '':
            data['email'] = None
        if 'phone' in data and data['phone'] == '':
            data['phone'] = None

        return super().to_representation(data)
