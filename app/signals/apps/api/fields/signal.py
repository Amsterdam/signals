# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2023 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
from collections import OrderedDict

from datapunt_api.serializers import LinksField
from drf_spectacular.utils import extend_schema_field
from rest_framework.request import Request
from rest_framework.reverse import reverse

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
                    'example': 'https://api.example.com/signals/v1/private/signals/2'
                }
            }
        },
        'archives': {
            'type': 'object',
            'properties': {
                'href': {
                    'type': 'string',
                    'format': 'uri',
                    'example': 'https://api.example.com/signals/v1/private/signals/2/history/'
                }
            }
        },
        'sia:attachments': {
            'type': 'object',
            'properties': {
                'href': {
                    'type': 'string',
                    'format': 'uri',
                    'example': 'https://api.example.com/signals/v1/private/signals/2/attachments/'
                }
            }
        },
        'sia:pdf': {
            'type': 'object',
            'properties': {
                'href': {
                    'type': 'string',
                    'format': 'uri',
                    'example': 'https://api.example.com/signals/v1/private/signals/2/pdf/'
                }
            }
        },
        'sia:context': {
            'type': 'object',
            'properties': {
                'href': {
                    'type': 'string',
                    'format': 'uri',
                    'example': 'https://api.example.com/signals/v1/private/signals/2/context/'
                }
            }
        },
        'sia:parent': {
            'type': 'object',
            'properties': {
                'href': {
                    'type': 'string',
                    'format': 'uri',
                    'example': 'https://api.example.com/signals/v1/private/signals/1'
                }
            }
        },
        'sia:children': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'href': {
                        'type': 'string',
                        'format': 'uri',
                        'example': 'https://api.example.com/signals/v1/private/signals/3'
                    }
                }
            },
            'minItems': 0
        },
    }
})
class PrivateSignalLinksFieldWithArchives(LinksField):
    def to_representation(self, value: Signal) -> OrderedDict:
        request = self.context.get('request')
        assert isinstance(request, Request)

        result = OrderedDict([
            ('curies', {'name': 'sia', 'href': reverse('signal-namespace', request=request)}),
            ('self', {'href': self.get_url(value, 'private-signals-detail', request, None)}),
            ('archives', {'href': self.get_url(value, "private-signals-history", request, None)}),
            ('sia:attachments', {
                'href': reverse(
                    'private-signals-attachments-list',
                    kwargs={'parent_lookup__signal__pk': value.pk},
                    request=request,
                )
            }),
            ('sia:pdf', {'href': self.get_url(value, "private-signals-pdf-download", request, None)}),
            ('sia:context', {'href': self.get_url(value, 'private-signal-context', request, None)}),
        ])

        if value.is_child:
            assert value.parent is not None
            result.update({
                'sia:parent':
                    {'href': self.get_url(value.parent, "private-signals-detail", request, None)}
            })

        if value.is_parent:
            result.update({'sia:children': [
                {'href': self.get_url(child, "private-signals-detail", request, None)}
                for child in value.children.all()
            ]})

        return result


@extend_schema_field({
    'type': 'object',
    'properties': {
        'self': {
            'type': 'object',
            'properties': {
                'href': {
                    'type': 'string',
                    'format': 'uri',
                    'example': 'https://api.example.com/signals/v1/private/signals/1'
                }
            }
        }
    }
})
class PrivateSignalLinksField(LinksField):
    def to_representation(self, value: Signal) -> OrderedDict:
        request = self.context.get('request')
        assert isinstance(request, Request)

        result = OrderedDict([
            ('self', {'href': self.get_url(value, "private-signals-detail", request, None)}),
        ])

        return result


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
                    'example': 'https://api.example.com/signals/v1/private/signals/1'
                }
            }
        },
        'sia:context-reporter-detail': {
            'type': 'object',
            'properties': {
                'href': {
                    'type': 'string',
                    'format': 'uri',
                    'example': 'https://api.example.com/signals/v1/private/signals/1/context/reporter/'
                }
            }
        },
        'sia:context-geography-detail': {
            'type': 'object',
            'properties': {
                'href': {
                    'type': 'string',
                    'format': 'uri',
                    'example': 'https://api.example.com/signals/v1/private/signals/1/context/near/geography/'
                }
            }
        },
    }
})
class PrivateSignalWithContextLinksField(LinksField):
    def to_representation(self, value: Signal) -> OrderedDict:
        request = self.context.get('request')
        assert isinstance(request, Request)

        result = OrderedDict([
            ('curies', {'name': 'sia', 'href': reverse('signal-namespace', request=request)}),
            ('self', {'href': self.get_url(value, 'private-signal-context', request, None)}),
            ('sia:context-reporter-detail', {
                'href': self.get_url(value, 'private-signal-context-reporter', request, None)
            }),
            ('sia:context-geography-detail', {
                'href': self.get_url(value, 'private-signal-context-near-geography', request, None)
            }),
        ])

        return result


class PublicSignalLinksField(LinksField):
    lookup_field = 'signal_id'

    def to_representation(self, value: Signal) -> OrderedDict:
        request = self.context.get('request')
        assert isinstance(request, Request)

        result = OrderedDict([
            ('self', {'href': self.get_url(value, "public-signals-detail", request, None)}),
        ])

        return result
