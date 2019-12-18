from signals.settings.base import *  # noqa

# Django security settings
SECURE_SSL_REDIRECT = True
SECURE_REDIRECT_EXEMPT = [r'^status/', ]  # Allow health checks on localhost.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Full text search is not yet enabled on our production environment.
# TODO: remove this override of the base settings when appropriate
FEATURE_FLAGS['API_SEARCH_ENABLED'] = False  # noqa F405
FEATURE_FLAGS['SEARCH_BUILD_INDEX'] = False  # noqa F405

# Filter extra properties is not yet enabled for production
FEATURE_FLAGS['API_FILTER_EXTRA_PROPERTIES'] = False  # noqa F405
