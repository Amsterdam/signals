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
]
MIDDLEWARE.append(  # noqa
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

TEST_LOGIN = os.getenv('TEST_LOGIN', 'signals.admin@example.com')

IMAGEKIT_DEFAULT_CACHEFILE_STRATEGY = 'imagekit.cachefiles.strategies.Optimistic'


def show_toolbar(request):
    return True


DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': show_toolbar,
}


try:
    from signals.settings.local import *  # noqa
except ImportError:
    pass
