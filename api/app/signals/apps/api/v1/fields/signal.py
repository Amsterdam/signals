from collections import OrderedDict

from rest_framework import serializers


class PrivateSignalLinksFieldWithArchives(serializers.HyperlinkedIdentityField):
    def to_representation(self, value):
        request = self.context.get('request')

        result = OrderedDict([
            ('curies', dict(name='sia', href=self.reverse("signal-namespace", request=request))),
            ('self', dict(href=self.get_url(value, "private-signals-detail", request, None))),
            ('archives', dict(href=self.get_url(value, "private-signals-history", request, None))),
            ('sia:attachments',
             dict(href=self.get_url(value, "private-signals-attachments", request, None))),
            ('sia:pdf', dict(href=self.get_url(value, "signal-pdf-download", request, None))),
        ])

        if value.is_child():
            result.update({
                'sia:parent':
                dict(href=self.get_url(value.parent, "private-signals-detail", request, None))
            })

        if value.is_parent():
            result.update({'sia:children': [
                dict(href=self.get_url(child, "private-signals-detail", request, None))
                for child in value.children.all()
            ]})

        return result


class PrivateSignalLinksField(serializers.HyperlinkedIdentityField):

    def to_representation(self, value):
        request = self.context.get('request')

        result = OrderedDict([
            ('self', dict(href=self.get_url(value, "v1:private-signals-detail", request, None))),
        ])

        return result


class PublicSignalLinksField(serializers.HyperlinkedIdentityField):
    lookup_field = 'signal_id'

    def to_representation(self, value):
        request = self.context.get('request')

        result = OrderedDict([
            ('self', dict(href=self.get_url(value, "public-signals-detail", request, None))),
        ])

        return result
