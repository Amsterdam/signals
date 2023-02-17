# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from rest_framework.throttling import SimpleRateThrottle


class AnonMySignalsTokenRateThrottle(SimpleRateThrottle):
    """
    Limits the rate of API calls that may be made by an anonymous reporter.

    The IP address of the request will be used as the unique cache key.
    """
    scope = 'anon-my_signals'

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            return None  # Only throttle unauthenticated requests.

        return self.cache_format % {
            'scope': self.scope,
            'ident': self.get_ident(request)
        }

    def parse_rate(self, rate):
        """
        Added the possibility to add a "quarter" to the rate for anonymous calls to the my signal token
        """
        if rate is None:
            return (None, None)
        num, period = rate.split('/')
        num_requests = int(num)
        duration = {'s': 1, 'm': 60, 'q': 900, 'h': 3600, 'd': 86400}[period[0:1]]
        return (num_requests, duration)
