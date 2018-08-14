from celery.schedules import crontab

from signals.messaging.categories import SUB_CATEGORIES_DICT
from signals.settings_common import *  # noqa F403
from signals.settings_common import INSTALLED_APPS
from signals.settings_databases import (
    LocationKey,
    get_docker_host,
    get_database_key,
    OVERRIDE_HOST_ENV_VAR,
    OVERRIDE_PORT_ENV_VAR,
    in_docker)

# Application definition
INSTALLED_APPS += (
    'drf_yasg',
    'storages',
    'signals.apps.health',
    'signals.apps.signals',
)

ROOT_URLCONF = 'signals.urls'
WSGI_APPLICATION = 'signals.wsgi.application'

DATABASE_OPTIONS = {
    LocationKey.docker: {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": os.getenv("DATABASE_NAME", "signals"),
        "USER": os.getenv("DATABASE_USER", "signals"),
        "PASSWORD": os.getenv("DATABASE_PASSWORD", "insecure"),
        "HOST": "database",
        "PORT": "5432",
    },
    LocationKey.local: {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": os.getenv("DATABASE_NAME", "signals"),
        "USER": os.getenv("DATABASE_USER", "signals"),
        "PASSWORD": os.getenv("DATABASE_PASSWORD", "insecure"),
        "HOST": get_docker_host(),
        "PORT": "5409",
    },
    LocationKey.override: {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": os.getenv("DATABASE_NAME", "signals"),
        "USER": os.getenv("DATABASE_USER", "signals"),
        "PASSWORD": os.getenv("DATABASE_PASSWORD", "insecure"),
        "HOST": os.getenv(OVERRIDE_HOST_ENV_VAR),
        "PORT": os.getenv(OVERRIDE_PORT_ENV_VAR, "5432"),
    },
}

# Object store / Swift
if os.getenv("SWIFT_ENABLED", "false") == "true":
    DEFAULT_FILE_STORAGE = 'swift.storage.SwiftStorage'
    SWIFT_USERNAME = os.getenv("SWIFT_USERNAME")
    SWIFT_PASSWORD = os.getenv("SWIFT_PASSWORD")
    SWIFT_AUTH_URL = os.getenv("SWIFT_AUTH_URL")
    SWIFT_TENANT_ID = os.getenv("SWIFT_TENANT_ID")
    SWIFT_TENANT_NAME = os.getenv("SWIFT_TENANT_NAME")
    SWIFT_REGION_NAME = os.getenv("SWIFT_REGION_NAME")
    SWIFT_CONTAINER_NAME = os.getenv("SWIFT_CONTAINER_NAME")
    SWIFT_TEMP_URL_KEY = os.getenv("SWIFT_TEMP_URL_KEY")
    SWIFT_USE_TEMP_URLS = True
else:
    # noinspection PyUnresolvedReferences
    MEDIA_ROOT = '/tmp/signals/upload'

# Object store - Datawarehouse (DWH)
DWH_SWIFT_AUTH_URL = os.getenv('SWIFT_AUTH_URL')
DWH_SWIFT_USERNAME = os.getenv('DWH_SWIFT_USERNAME')
DWH_SWIFT_PASSWORD = os.getenv('DWH_SWIFT_PASSWORD')
DWH_SWIFT_TENANT_NAME = os.getenv('DWH_SWIFT_TENANT_NAME')
DWH_SWIFT_TENANT_ID = os.getenv('DWH_SWIFT_TENANT_ID')
DWH_SWIFT_REGION_NAME = os.getenv('SWIFT_REGION_NAME')
DWH_SWIFT_CONTAINER_NAME = os.getenv('DWH_SWIFT_CONTAINER_NAME')

# Database

DATABASES = {"default": DATABASE_OPTIONS[get_database_key()]}

STATIC_URL = '/signals/static/'

# noinspection PyUnresolvedReferences
STATIC_ROOT = '/static/'

HEALTH_MODEL = "signals.Signal"  # TODO what is this thing?

# The following JWKS data was obtained in the authz project :  jwkgen -create -alg ES256   # noqa
# This is a test public/private key def and added for testing .
JWKS_TEST_KEY = """
    {
        "keys": [
            {
                "kty": "EC",
                "key_ops": [
                    "verify",
                    "sign"
                ],
                "kid": "2aedafba-8170-4064-b704-ce92b7c89cc6",
                "crv": "P-256",
                "x": "6r8PYwqfZbq_QzoMA4tzJJsYUIIXdeyPA27qTgEJCDw=",
                "y": "Cf2clfAfFuuCB06NMfIat9ultkMyrMQO9Hd2H7O9ZVE=",
                "d": "N1vu0UQUp0vLfaNeM0EDbl4quvvL6m_ltjoAXXzkI3U="
            }
        ]
    }
"""

DATAPUNT_AUTHZ = {
    'JWKS': os.getenv('PUB_JWKS', JWKS_TEST_KEY),
    'ALWAYS_OK': LOCAL
}

SWAGGER_SETTINGS = {
    'USE_SESSION_AUTH': False,
    'SECURITY_DEFINITIONS': {
        'Signals API - Swagger': {
            'type': 'oauth2',
            'authorizationUrl': DATAPUNT_API_URL + "oauth2/authorize",
            'flow': 'implicit',
            'scopes': {
                'SIG/ALL': 'Signals alle authorizaties',
            }
        }
    },
    'OAUTH2_CONFIG': {
        'clientId': 'swagger-ui',
        #  'clientSecret': 'yourAppClientSecret',
        'appName': 'Signal Swagger UI',
    },
}

# E-mail settings for SMTP (SendGrid)
INSTALLED_APPS += (
    'djcelery_email',
    'django_celery_beat',
    'django_celery_results',
)
EMAIL_BACKEND = 'djcelery_email.backends.CeleryEmailBackend'

RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'signals')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'insecure')
RABBITMQ_VHOST = os.getenv('RABBITMQ_VHOST', 'vhost')
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST',
                          'rabbit' if in_docker() else 'localhost')

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL',
                              f'amqp://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}'
                              f'@{RABBITMQ_HOST}/{RABBITMQ_VHOST}')
CELERY_EMAIL_CHUNK_SIZE = 1

# Celery Beat settings.
CELERY_RESULT_BACKEND = 'django-db'
CELERY_TASK_RESULT_EXPIRES = 604800  # 7 days in seconds (7*24*60*60)
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_BEAT_SCHEDULE = {
    'save-csv-files-datawarehouse': {
        'task': 'signals.apps.signals.tasks'
                '.task_save_csv_files_datawarehouse',
        'schedule': crontab(hour=4),
    },
}

if TESTING:
    CELERY_TASK_ALWAYS_EAGER = True

# CELERY_EMAIL_TASK_CONFIG = {
#     'queue': 'email',
#     'rate_limit': '50/m',  # * CELERY_EMAIL_CHUNK_SIZE (default: 10)
# }

# Can locally be tested with a Google account, for example :
#
# export EMAIL_HOST=smtp.gmail.com
# export EMAIL_HOST_USER=<gmail_account>
# export EMAIL_HOST_PASSWORD=<gmail_password>
# export EMAIL_PORT=465
# export EMAIL_USE_SSL=True
# export EMAIL_USE_TLS=False
#
# These exports have to be set for the task that realy does the sending. So if
# celery  does the sending then then these export should be set before starting
# the celery working process

SIGMAX_AUTH_TOKEN = os.getenv('SIGMAX_AUTH_TOKEN', None)
SIGMAX_SERVER = os.getenv('SIGMAX_SERVER', None)

EMAIL_APPTIMIZE_INTEGRATION_ADDRESS = os.getenv(
    'EMAIL_APPTIMIZE_INTEGRATION_ADDRESS', None)
EMAIL_FLEX_HORECA_INTEGRATION_ADDRESS = os.getenv(
    'EMAIL_FLEX_HORECA_INTEGRATION_ADDRESS', None)
NOREPLY = 'noreply@meldingen.amsterdam.nl'

EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
EMAIL_PORT = os.getenv('EMAIL_PORT', 465)  # 465 fort SSL 587 for TLS

EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', False)
if not EMAIL_USE_TLS:
    EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', True)

TESTING = sys.argv[1:2] == ['test']

# Use custom User Model for Signals
# AUTH_USER_MODEL = "signals.SignalsUser"

ADMIN_LOGIN = "signals.admin@amsterdam.nl"

# TEST_LOGIN = os.getenv("TEST_LOGIN", "signals.behandelaar@amsterdam.nl")
# TEST_LOGIN = os.getenv("TEST_LOGIN", "signals.coordinator@amsterdam.nl")
# TEST_LOGIN = os.getenv("TEST_LOGIN", "signals.monitor@amsterdam.nl")
TEST_LOGIN = os.getenv("TEST_LOGIN", "signals.admin@amsterdam.nl")
# TEST_LOGIN = os.getenv("TEST_LOGIN", "invalid@invalid.nl")

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
