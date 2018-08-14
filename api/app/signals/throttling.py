from rest_framework.throttling import SimpleRateThrottle


class NoUserRateThrottle(SimpleRateThrottle):
    """
    Limits the rate of API calls that does not look at the user.

    The IP address of the request will be used as the unique cache key.
    """
    scope = 'nouser'

    def get_cache_key(self, request, view):
        return self.cache_format % {
            'scope': self.scope,
            'ident': self.get_ident(request)
        }
