from collections import OrderedDict

from rest_framework import serializers


class UserHyperlinkedIdentityField(serializers.HyperlinkedIdentityField):
    def to_representation(self, value):
        request = self.context.get('request')

        result = OrderedDict([
            ('curies', dict(name='sia', href=self.reverse('signal-namespace', request=request))),
            ('self', dict(
                href=self.get_url(value, 'user-detail', request, None),
             )),
            # ('archives', dict(href=self.get_url(value, 'user-history', request, None))),
        ])

        return result
