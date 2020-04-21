import os
from datetime import timedelta

from signals.settings.base import *  # noqa

SECRET_KEY = 'insecure'
DEBUG = True
ALLOWED_HOSTS = ['*']
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Simple JWT supports RSA and PEM notation
JWT_RSA_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA7WWwOFhc0R3YwVPCRrRw
RkSN5VJEv/83DdBa8r7ooK8Pn204ssaQjAJ7kenO0z1Lium7kVOjvPGpVk3RgIAt
opQxx1Eo4WmYybjpYgmk9pghdgMeKXGdPY90UFuSN2KmpB4jebUxXzhliXV9L75S
saltCHInW3ytfam9ZQaquwuyxQOvJ4L1Qy8yHXzoca1nL++bZBgw+ILvMyxMU3C5
HSHNZb3TyW/qP0fr1AIw5r5MWTSoTt+8DuXmjleyEDxpscmeSLKljrl8COuW/Dji
LLesaDQsfeDlONWoR2TpoW3cDf8/nAH6DxHD/T3gr7ceaIEECCKbe+8KZktBxdDx
TQIDAQAB
-----END PUBLIC KEY-----"""

# 'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=14),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
    'ALGORITHM': 'RS256',
    'SIGNING_KEY': None,
    'VERIFYING_KEY': JWT_RSA_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'email',
    'USER_ID_CLAIM': 'email',
    'AUTH_TOKEN_CLASSES': ('signals.auth.backend.JWTBearerTokenVerify',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

SITE_DOMAIN = 'localhost:8000'

INSTALLED_APPS += [  # noqa
    'debug_toolbar',
]
MIDDLEWARE.append(  # noqa
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

TEST_LOGIN = os.getenv('TEST_LOGIN', 'signals.admin@example.com')

IMAGEKIT_DEFAULT_CACHEFILE_STRATEGY = 'imagekit.cachefiles.strategies.Optimistic'

# ML_TOOL_ENDPOINT = 'https://acc.api.data.amsterdam.nl/signals_mltool'

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
