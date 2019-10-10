from collections import OrderedDict

from rest_framework import serializers


class UserHyperlinkedIdentityField(serializers.HyperlinkedIdentityField):

    def to_representation(self, value):
        request = self.context.get('request')

        result = OrderedDict([
            ('self', dict(
                href=self.get_url(value, 'user-detail', request, None))
             ),
        ])

        return result
