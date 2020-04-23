import os

from signals.settings.base import *  # noqa

SECRET_KEY = 'insecure'
DEBUG = True
ALLOWED_HOSTS = ['*']
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

JWKS_TEST_KEY = """
    {
        "keys": [
            {
            "use": "sig",
            "kty": "RSA",
            "kid": "b47e41f2b869ad8b0ff4f7f181d339faa571c0df",
            "alg": "RS256",
            "n": "p4HXNA3O0_CRSwMezkzVkNlvBFcTJpabb25GA6bcgsnMjFRc_fpZ7q9WnJh_IOLmmObyvHuZQp4Am7k5Z6oujVi5x8kLQW8jmusg4cn5_B7WlqMxhtfHtg6ipCpfs2-ni0xnHer_79YgntBTYk5XTF3wBnEdGGB5tBYls3CenGG0xExUWYtL_tE7aYnaDIWuINXxuEnCwiitV4W_WMtP-Ql1Ul2BvPziwNcKBKPVUPx3Rix-ZoBI05zuG2mcxD9H0fB_8-ndj23YPLGrD9N-Q7L3ZVa_WRod1PtitPRqa2JdhLSygTUNu-tC85ILbtEsaUnjjc-7M9Fa7rHSqOxYaw", # noqa: E501
            "e": "AQAB"
            }
        ]
    }
"""

SIGNALS_AUTHZ = {
    'JWKS': os.getenv('PUB_JWKS', JWKS_TEST_KEY),
    'ALWAYS_OK': False,
    'USER_ID_FIELD': 'email'
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
