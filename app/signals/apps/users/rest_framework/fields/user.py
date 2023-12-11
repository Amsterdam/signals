# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2023 Gemeente Amsterdam
from collections import OrderedDict

from datapunt_api.serializers import LinksField
from django.contrib.auth.models import User
from drf_spectacular.utils import extend_schema_field
from rest_framework.reverse import reverse


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
    }
})
class UserLinksField(LinksField):
    def to_representation(self, value: User) -> OrderedDict:
        request = self.context.get('request')

        result = OrderedDict([
            ('curies', {'name': 'sia', 'href': reverse('signal-namespace', request=request)}),
            ('self', {'href': self.get_url(value, 'user-detail', request, None)}),
        ])

        return result
