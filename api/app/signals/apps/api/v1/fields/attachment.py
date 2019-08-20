from collections import OrderedDict

from rest_framework import serializers

from signals.apps.signals.models import Attachment


class PublicSignalAttachmentLinksField(serializers.HyperlinkedIdentityField):
    lookup_field = 'signal_id'

    def to_representation(self, value: Attachment):
        request = self.context.get('request')

        result = OrderedDict([
            ('self',
             dict(href=self.get_url(value._signal, "public-signals-attachments", request, None))),
        ])

        return result


class PrivateSignalAttachmentLinksField(serializers.HyperlinkedIdentityField):
    def to_representation(self, value: Attachment):
        request = self.context.get('request')

        result = OrderedDict([
            ('self',
             dict(href=self.get_url(value._signal, "private-signals-attachments", request, None))),
        ])

        return result
