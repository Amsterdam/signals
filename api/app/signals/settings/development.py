# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2021 Gemeente Amsterdam
import os

from signals.settings.base import *  # noqa

SITE_DOMAIN = 'localhost:8000'
SECRET_KEY = 'insecure'
DEBUG = True
ALLOWED_HOSTS = ['*', ]
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
DATABASES['default']['HOST'] = 'database'  # noqa: F405
DATABASES['default']['PORT'] = '5432'  # noqa: F405
SIGNALS_AUTH = {
    'JWKS_URL': os.getenv('JWKS_URL', 'http://dex:5556/keys'),
    'ALWAYS_OK': os.getenv('ALWAYS_OK', True) in TRUE_VALUES,  # noqa
    'USER_ID_FIELDS': os.getenv('USER_ID_FIELDS', 'email').split(',')
}
TEST_LOGIN = os.getenv('TEST_LOGIN', 'signals.admin@example.com')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://dummy_link')

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

try:
    from signals.settings.local import *  # noqa
except ImportError:
    pass
