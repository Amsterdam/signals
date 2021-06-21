# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2021 Gemeente Amsterdam
import os

from signals.settings.base import *  # noqa

SECRET_KEY = 'insecure'
DEBUG = True
ALLOWED_HOSTS = ['*']
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')

SIGNALS_AUTHZ = {
    'JWKS': JWKS_TEST_KEY,  # noqa
    'JWKS_URL': os.getenv('JWKS_URL', 'http://dex:5556/keys'),
    'ALWAYS_OK': os.getenv('ALWAYS_OK', 'False') in ['True', 'true', '1'],
    'USER_ID_FIELDS': os.getenv('USER_ID_FIELDS', 'email').split(',')
}

SITE_DOMAIN = 'localhost:8000'

INSTALLED_APPS += [  # noqa
    'debug_toolbar',
]
MIDDLEWARE.append(  # noqa
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

TEST_LOGIN = os.getenv('TEST_LOGIN', 'signals.admin@example.com')

# ML_TOOL_ENDPOINT = 'https://acc.api.data.amsterdam.nl/signals_mltool'

FRONTEND_URL = os.getenv('FRONTEND_URL', 'https://acc.meldingen.amsterdam.nl')

try:
    from signals.settings.local import *  # noqa
except ImportError:
    pass


def show_toolbar(request):
    return False  # True to enable Django Debug Toolbar (very slow)


DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': show_toolbar,
}

# Set console logging to DEBUG
LOGGING['handlers'].update({  # noqa F405
    'console': {
        'level': 'WARNING',
        'class': 'logging.StreamHandler',
        'formatter': 'console',
    },
})

# Log queries to the console
LOGGING['loggers'].update({  # noqa F405
    'django.db.backends': {
        'level': 'WARNING',
        'handlers': ['console', ],
    }
})
