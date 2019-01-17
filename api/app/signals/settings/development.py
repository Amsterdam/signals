import os

from signals.settings.base import *  # noqa

from .zds import *  # noqa

SECRET_KEY = 'insecure'
DEBUG = True
ALLOWED_HOSTS = ['*']
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DATAPUNT_AUTHZ['ALWAYS_OK'] = True  # noqa
SITE_DOMAIN = 'localhost:8000'

INSTALLED_APPS += [  # noqa
    'debug_toolbar',
    'signals.apps.zds',
]
MIDDLEWARE.append(  # noqa
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

TEST_LOGIN = os.getenv('TEST_LOGIN', 'signals.admin@amsterdam.nl')
# TEST_LOGIN = os.getenv('TEST_LOGIN', 'signals.behandelaar@amsterdam.nl')
# TEST_LOGIN = os.getenv('TEST_LOGIN', 'signals.coordinator@amsterdam.nl')
# TEST_LOGIN = os.getenv('TEST_LOGIN', 'signals.monitor@amsterdam.nl')
# TEST_LOGIN = os.getenv('TEST_LOGIN', 'invalid@invalid.nl')

IMAGEKIT_DEFAULT_CACHEFILE_STRATEGY = 'imagekit.cachefiles.strategies.Optimistic'

try:
    from signals.settings.local import *  # noqa
except ImportError:
    pass
