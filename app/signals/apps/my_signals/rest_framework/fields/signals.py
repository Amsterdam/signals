# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 - 2023 Gemeente Amsterdam
from collections import OrderedDict

from drf_spectacular.utils import extend_schema_field
from rest_framework.relations import HyperlinkedIdentityField

from signals.apps.signals.models import Signal


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
                    'example': 'https://api.example.com/signals/v1/my/signals/358f6855-61b7-4a6e-b2b3-1737b63b93e9'
                }
            }
        },
    }
})
class MySignalListLinksField(HyperlinkedIdentityField):
    lookup_field = 'uuid'

    def to_representation(self, value: Signal) -> OrderedDict:
        request = self.context.get('request')
        _format = self.context.get('format')

        return OrderedDict([
            ('curies', dict(name='sia', href=self.reverse('signal-namespace', request=request, format=_format))),
            ('self', dict(href=self.get_url(value, 'my_signals:my-signals-detail', request, _format))),
        ])


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
                    'example': 'https://api.example.com/signals/v1/my/signals/358f6855-61b7-4a6e-b2b3-1737b63b93e9'
                }
            }
        },
        'archives': {
            'type': 'object',
            'properties': {
                'href': {
                    'type': 'string',
                    'format': 'uri',
                    'example': 'https://api.example.com/signals/v1/my/signals/358f6855-61b7-4a6e-b2b3-1737b63b93e9'
                               '/history'
                }
            }
        },
        'sia:attachments': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'href': {
                        'type': 'string',
                        'format': 'uri',
                        'example': 'https://api.example.com/media/1.png'
                    },
                    'created_by': {
                        'type': 'string',
                        'example': 'john.doe@example.com'
                    },
                    'created_at': {
                        'type': 'string',
                        'format': 'date-time',
                        'example': '2023-06-01T00:00:00Z'
                    },
                    'caption': {
                        'type': 'string',
                        'nullable': True,
                        'example': 'This is a caption',
                    }
                }
            }
        },
    }
})
class MySignalDetailLinksField(HyperlinkedIdentityField):
    lookup_field = 'uuid'

    def to_representation(self, value: Signal) -> OrderedDict:
        request = self.context.get('request')
        _format = self.context.get('format')

        representation = OrderedDict([
            ('curies', dict(name='sia', href=self.reverse('signal-namespace', request=request, format=_format))),
            ('self', dict(href=self.get_url(value, 'my_signals:my-signals-detail', request, _format))),
            ('archives', dict(href=self.get_url(value, 'my_signals:my-signals-history', request, _format))),
        ])

        attachment_qs = value.attachments.filter(public=True)
        if attachment_qs.exists():
            # A list URI's of all the attachments
            representation.update({
                ('sia:attachments', (
                    {
                        'href': request.build_absolute_uri(attachment.file.url),
                        'created_by': attachment.created_by,
                        'created_at': attachment.created_at,
                        'caption': attachment.caption,
                    }
                    for attachment in attachment_qs.all().order_by('-created_at')
                )),
            })

        return representation
