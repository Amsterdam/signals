# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2021 Gemeente Amsterdam
from rest_framework.throttling import SimpleRateThrottle


class PostOnlyNoUserRateThrottle(SimpleRateThrottle):
    """
    Limits the rate of API calls that does not look at the user.

    The IP address of the request will be used as the unique cache key.
    """

    scope = 'nouser'

    def allow_request(self, request, view):
        if request.method == 'POST':
            return super().allow_request(request, view)
        return True

    def get_cache_key(self, request, view):
        return self.cache_format % {
            'scope': self.scope,
            'ident': self.get_ident(request)
        }
