import os

from signals.settings.base import *  # noqa

# Django security settings
SECURE_SSL_REDIRECT = True
SECURE_REDIRECT_EXEMPT = [r'^status/', ]  # Allow health checks on localhost.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Filter extra properties is not yet enabled for production
FEATURE_FLAGS['API_FILTER_EXTRA_PROPERTIES'] = False  # noqa F405
SIGNALS_AUTHZ['USER_ID_FIELDS'] = os.getenv('USER_ID_FIELDS', 'sub,email').split(',')  # noqa F405
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = ('signals.throttling.NoUserRateThrottle',) # noqa
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {'nouser': '1/min'} # noqa
