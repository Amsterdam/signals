from signals.settings.base import *  # noqa

SECRET_KEY = 'insecure'
DEBUG = True
ALLOWED_HOSTS = ['*']
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DATAPUNT_AUTHZ['ALWAYS_OK'] = True

INSTALLED_APPS.append(
    'debug_toolbar'
)
MIDDLEWARE.append(
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

try:
    from signals.settings.local_settings import *  # noqa
except ImportError:
    pass
