# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2023 Gemeente Amsterdam
from collections import OrderedDict

from django.urls import reverse
from rest_framework.response import Response
from rest_framework.routers import APIRootView
from rest_framework_extensions.routers import ExtendedDefaultRouter

from signals import __version__


class BaseSignalsAPIRootView(APIRootView):
    def get(self, request, *args, **kwargs):
        data = OrderedDict({
            'v1': {
                '_links': {
                    'self': {
                        'href': request._request.build_absolute_uri(reverse('api-root')),
                    }
                },
                'version': __version__,
                'status': 'in production',
            },
            'version': __version__,
        })

        return Response(data)

    def get_view_name(self):
        return 'Signals API'


class SignalsRouter(ExtendedDefaultRouter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trailing_slash = '/?'
