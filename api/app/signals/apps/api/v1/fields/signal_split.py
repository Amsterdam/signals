"""
Signals API V1 custom serializer fields.
"""
from collections import OrderedDict

from rest_framework import serializers

from signals.apps.signals.models import Signal


class PrivateSignalSplitLinksField(serializers.HyperlinkedIdentityField):
    def to_representation(self, signal: Signal):
        request = self.context.get('request')

        result = OrderedDict([
            ('self',
             dict(href=self.get_url(signal, "v1:private-signals-split", request, None))),
        ])

        return result
