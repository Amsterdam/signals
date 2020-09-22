from signals.settings.base import *  # noqa

# Django security settings
SECURE_SSL_REDIRECT = True
SECURE_REDIRECT_EXEMPT = [r'^status/', ]  # Allow health checks on localhost.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Filter extra properties is not yet enabled for production
FEATURE_FLAGS['API_FILTER_EXTRA_PROPERTIES'] = False  # noqa F405
