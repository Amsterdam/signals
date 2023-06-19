# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2023 Gemeente Amsterdam
from collections import OrderedDict

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers


@extend_schema_field({
    'type': 'object',
    'properties': {
        'curies': {
            'type': 'object',
            'properties': {
                'href': {
                    'type': 'string',
                    'format': 'uri',
                    'example': 'https://api.example.com/signals/relations/'
                }
            }
        },
        'self': {
            'type': 'object',
            'properties': {
                'href': {
                    'type': 'string',
                    'format': 'uri',
                    'example': 'https://api.example.com/signals/v1/private/user/1'
                }
            }
        },
        # 'archives': {
        #     'type': 'object',
        #     'properties': {
        #         'href': {
        #             'type': 'string',
        #             'format': 'uri',
        #             'example': 'https://api.example.com/signals/v1/private/user/1/history/'
        #         }
        #     }
        # },
    }
})
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
