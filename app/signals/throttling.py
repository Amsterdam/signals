# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2023 Gemeente Amsterdam
import logging

from rest_framework.request import Request
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView

logger = logging.getLogger('django')


class PostOnlyNoUserRateThrottle(SimpleRateThrottle):
    """Limits the rate of API calls that does not look at the user.
    The IP address of the request will be used as the unique cache key."""
    scope: str = 'nouser'

    def allow_request(self, request: Request, view: APIView) -> bool:
        allow = True

        if request.method == 'POST':
            allow = super().allow_request(request, view)

        if allow:
            logger.debug(f'PostOnlyNoUserRateThrottle: allowing request for: {self.get_cache_key(request, view)}')
        else:
            logger.debug(f'PostOnlyNoUserRateThrottle: not allowing request for: {self.get_cache_key(request, view)}')

        return allow

    def get_ident(self, request: Request) -> str:
        ident = super().get_ident(request=request)
        last_colon_index = ident.rfind(":")
        return ident[:last_colon_index] if last_colon_index != -1 else ident

    def get_cache_key(self, request, view) -> str:
        return self.cache_format % {
            'scope': self.scope,
            'ident': self.get_ident(request)
        }
