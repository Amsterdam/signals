import os

from signals.settings.base import *  # noqa

SECRET_KEY = 'insecure'
DEBUG = True
ALLOWED_HOSTS = ['*']
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DATAPUNT_AUTHZ['ALWAYS_OK'] = True  # noqa

INSTALLED_APPS.append(  # noqa
    'debug_toolbar'
)
MIDDLEWARE.append(  # noqa
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

TEST_LOGIN = os.getenv('TEST_LOGIN', 'signals.admin@amsterdam.nl')
# TEST_LOGIN = os.getenv('TEST_LOGIN', 'signals.behandelaar@amsterdam.nl')
# TEST_LOGIN = os.getenv('TEST_LOGIN', 'signals.coordinator@amsterdam.nl')
# TEST_LOGIN = os.getenv('TEST_LOGIN', 'signals.monitor@amsterdam.nl')
# TEST_LOGIN = os.getenv('TEST_LOGIN', 'invalid@invalid.nl')

try:
    from signals.settings.local import *  # noqa
except ImportError:
    pass
