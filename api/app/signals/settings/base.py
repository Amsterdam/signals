import os

from celery.schedules import crontab

from signals import API_VERSIONS
from signals.settings.settings_databases import (
    OVERRIDE_HOST_ENV_VAR,
    OVERRIDE_PORT_ENV_VAR,
    LocationKey,
    get_database_key,
    get_docker_host,
    in_docker
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Django settings
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = False
ALLOWED_HOSTS = [
    'api.data.amsterdam.nl',
    'acc.api.data.amsterdam.nl',

    # Currently this is needed because the deployment process checks the health endpoint with a
    # request to localhost:port.
    'localhost',
    '127.0.0.1',
]
ADMIN_LOGIN = 'signals.admin@amsterdam.nl'
INTERNAL_IPS = ('127.0.0.1', '0.0.0.0')
CORS_ORIGIN_ALLOW_ALL = True
SITE_ID = 1
SITE_NAME = 'Signalen API'
SITE_DOMAIN = os.getenv('SITE_DOMAIN', 'api.data.amsterdam.nl')

# Django security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Application definition
INSTALLED_APPS = [
    # Django
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.gis',

    # Signals project
    'signals.apps.email_integrations',
    'signals.apps.health',
    'signals.apps.signals',
    'signals.apps.users',
    'signals.apps.sigmax',
    'signals.apps.dashboards',

    # Third party
    'corsheaders',
    'datapunt_api',
    'django_celery_beat',
    'django_celery_results',
    'django_extensions',
    'django_filters',
    'djcelery_email',
    'drf_yasg',
    'imagekit',
    'raven.contrib.django.raven_compat',
    'rest_framework',
    'rest_framework_gis',
    # 'rest_framework_swagger',
    'storages',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.sites.middleware.CurrentSiteMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'authorization_django.authorization_middleware',
    'signals.apps.signals.middleware.APIVersionHeaderMiddleware',
]

ROOT_URLCONF = 'signals.urls'
WSGI_APPLICATION = 'signals.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ]
        },
    }
]

# Database
DATABASE_OPTIONS = {
    LocationKey.docker: {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('DATABASE_NAME', 'signals'),
        'USER': os.getenv('DATABASE_USER', 'signals'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', 'insecure'),
        'HOST': 'database',
        'PORT': '5432',
    },
    LocationKey.local: {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('DATABASE_NAME', 'signals'),
        'USER': os.getenv('DATABASE_USER', 'signals'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', 'insecure'),
        'HOST': get_docker_host(),
        'PORT': '5409',
    },
    LocationKey.override: {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('DATABASE_NAME', 'signals'),
        'USER': os.getenv('DATABASE_USER', 'signals'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', 'insecure'),
        'HOST': os.getenv(OVERRIDE_HOST_ENV_VAR),
        'PORT': os.getenv(OVERRIDE_PORT_ENV_VAR, '5432'),
    },
}
DATABASES = {
    'default': DATABASE_OPTIONS[get_database_key()]
}

# Internationalization
LANGUAGE_CODE = 'nl_NL'
TIME_ZONE = 'Europe/Amsterdam'
USE_I18N = True
USE_L10N = True
USE_TZ = True
DATETIME_FORMAT = 'l d-m-Y, H:i'  # e.g. "Donderdag 06-09-2018, 13:56"

# Static files (CSS, JavaScript, Images) and media files
STATIC_URL = '/signals/static/'
STATIC_ROOT = os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), 'static')
MEDIA_URL = '/signals/media/'
MEDIA_ROOT = os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), 'media')

# Object store / Swift
if os.getenv('SWIFT_ENABLED', 'false') == 'true':
    DEFAULT_FILE_STORAGE = 'swift.storage.SwiftStorage'
    SWIFT_USERNAME = os.getenv('SWIFT_USERNAME')
    SWIFT_PASSWORD = os.getenv('SWIFT_PASSWORD')
    SWIFT_AUTH_URL = os.getenv('SWIFT_AUTH_URL')
    SWIFT_TENANT_ID = os.getenv('SWIFT_TENANT_ID')
    SWIFT_TENANT_NAME = os.getenv('SWIFT_TENANT_NAME')
    SWIFT_REGION_NAME = os.getenv('SWIFT_REGION_NAME')
    SWIFT_CONTAINER_NAME = os.getenv('SWIFT_CONTAINER_NAME')
    SWIFT_TEMP_URL_KEY = os.getenv('SWIFT_TEMP_URL_KEY')
    SWIFT_USE_TEMP_URLS = True

# Object store - Datawarehouse (DWH)
DWH_SWIFT_AUTH_URL = os.getenv('SWIFT_AUTH_URL')
DWH_SWIFT_USERNAME = os.getenv('DWH_SWIFT_USERNAME')
DWH_SWIFT_PASSWORD = os.getenv('DWH_SWIFT_PASSWORD')
DWH_SWIFT_TENANT_NAME = os.getenv('DWH_SWIFT_TENANT_NAME')
DWH_SWIFT_TENANT_ID = os.getenv('DWH_SWIFT_TENANT_ID')
DWH_SWIFT_REGION_NAME = os.getenv('SWIFT_REGION_NAME')
DWH_SWIFT_CONTAINER_NAME = os.getenv('DWH_SWIFT_CONTAINER_NAME')

# Using `HEALTH_MODEL` for health check endpoint.
HEALTH_MODEL = 'signals.Signal'

HEALTH_MODEL_SUB_CATEGORY = 'signals.SubCategory'
HEALTH_MODEL_MAIN_CATEGORY = 'signals.MainCategory'
HEALTH_DATA_SUB_CATEGORY_MINIMUM_COUNT = 76
HEALTH_DATA_MAIN_CATEGORY_MINIMUM_COUNT = 9

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
    'ALWAYS_OK': False,
}

# Celery settings
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'signals')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'insecure')
RABBITMQ_VHOST = os.getenv('RABBITMQ_VHOST', 'vhost')
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbit' if in_docker() else 'localhost')

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL',
                              f'amqp://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}'
                              f'@{RABBITMQ_HOST}/{RABBITMQ_VHOST}')
CELERY_EMAIL_CHUNK_SIZE = 1
CELERY_RESULT_BACKEND = 'django-db'
CELERY_TASK_RESULT_EXPIRES = 604800  # 7 days in seconds (7*24*60*60)

# Celery Beat settings
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_BEAT_SCHEDULE = {
    'save-csv-files-datawarehouse': {
        'task': 'signals.apps.signals.tasks'
                '.task_save_csv_files_datawarehouse',
        'schedule': crontab(hour=4),
    },
}

# E-mail settings for SMTP (SendGrid)
EMAIL_BACKEND = 'djcelery_email.backends.CeleryEmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
EMAIL_PORT = os.getenv('EMAIL_PORT', 465)  # 465 fort SSL 587 for TLS
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', False)
if not EMAIL_USE_TLS:
    EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', True)

EMAIL_APPTIMIZE_INTEGRATION_ADDRESS = os.getenv('EMAIL_APPTIMIZE_INTEGRATION_ADDRESS', None)
EMAIL_FLEX_HORECA_INTEGRATION_ADDRESS = os.getenv('EMAIL_FLEX_HORECA_INTEGRATION_ADDRESS', None)
EMAIL_FLEX_HORECA_WEEKDAYS = os.getenv(
    'EMAIL_FLEX_HORECA_WEEKDAYS', '5,6,7')  # friday, saterday, sunday
EMAIL_FLEX_HORECA_END_TIME = os.getenv(
    'EMAIL_FLEX_HORECA_END_TIME', '04:00')  # 04:00 o'clock
EMAIL_HANDHAVING_OR_OOST_INTEGRATION_ADDRESS = os.getenv(
    'EMAIL_HANDHAVING_OR_OOST_INTEGRATION_ADDRESS', None)
EMAIL_TOEZICHT_OR_NIEUW_WEST_INTEGRATION_ADDRESS = os.getenv(
    'EMAIL_TOEZICHT_OR_NIEUW_WEST_INTEGRATION_ADDRESS', None)
EMAIL_VTH_NIEUW_WEST_INTEGRATION_ADDRESS = os.getenv(
    'EMAIL_VTH_NIEUW_WEST_INTEGRATION_ADDRESS', None)
NOREPLY = 'noreply@meldingen.amsterdam.nl'

# Django cache settings
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Sentry logging
RAVEN_CONFIG = {
    'dsn': os.getenv('SENTRY_RAVEN_DSN'),
}

# Django Logging settings
GELF_HOST: str = os.getenv('GELF_UDP_HOST', 'localhost')
GELF_PORT: int = int(os.getenv('GELF_UDP_PORT', '12201'))
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'gelf', 'sentry'],
    },
    'formatters': {
        'console': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    },
    'filters': {
        'static_fields': {
            '()': 'signals.utils.staticfieldfilter.StaticFieldFilter',
            'fields': {
                'project': 'SignalsAPI',
                'environment': 'Any',
                'hideme': 'True'
            },
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'console',
        },
        'sentry': {
            'level': 'WARNING',
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
        },
        'gelf': {
            'class': 'graypy.GELFHandler',
            'host': GELF_HOST,
            'port': GELF_PORT,
            'filters': ['static_fields'],
        }
    },
    'loggers': {
        'signals': {
            'level': 'WARNING',
            'handlers': ['console', 'gelf'],
            'propagate': True,
        },
        'django': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': True,
        },
        'raven': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'sentry.errors': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },

        # Debug all batch jobs
        'doc': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': False,
        },
        'index': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': False,
        },
        'search': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False,
        },
        'elasticsearch': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False,
        },
        'urllib3': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False,
        },
        'factory.containers': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': False,
        },
        'factory.generate': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'requests.packages.urllib3.connectionpool': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False,
        },

        # Log all unhandled exceptions
        'django.request': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False,
        },
    },
}

# Django REST framework settings
REST_FRAMEWORK = dict(
    PAGE_SIZE=100,
    MAX_PAGINATE_BY=100,
    UNAUTHENTICATED_USER={},
    UNAUTHENTICATED_TOKEN={},
    DEFAULT_AUTHENTICATION_CLASSES=(
        # 'signals.auth.backend.JWTAuthBackend',
        # 'rest_framework.authentication.BasicAuthentication',
        # 'rest_framework.authentication.SessionAuthentication',
    ),
    DEFAULT_PAGINATION_CLASS=(
        'datapunt_api.pagination.HALPagination',
    ),
    DEFAULT_RENDERER_CLASSES=(
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    DEFAULT_FILTER_BACKENDS=(
        # 'rest_framework.filters.SearchFilter',
        # 'rest_framework.filters.OrderingFilter',
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
    COERCE_DECIMAL_TO_STRING=True,
    DEFAULT_THROTTLE_CLASSES=(
        # Currently no default throttle class
        # 'signals.throttling.NoUserRateThrottle',
    ),
    DEFAULT_THROTTLE_RATES={
        # 'nouser': '5/hour',
        'nouser': '60/hour'
    },
    DEFAULT_VERSIONING_CLASS='rest_framework.versioning.NamespaceVersioning',
    DEFAULT_VERSION='v0',
    ALLOWED_VERSIONS=API_VERSIONS.keys(),
)

# Swagger settings
DATAPUNT_API_URL = os.getenv('DATAPUNT_API_URL', 'https://api.data.amsterdam.nl/')
SWAGGER_SETTINGS = {
    'USE_SESSION_AUTH': False,
    'SECURITY_DEFINITIONS': {
        'Signals API - Swagger': {
            'type': 'oauth2',
            'authorizationUrl': '{url}oauth2/authorize'.format(url=DATAPUNT_API_URL),
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

# Sigmax settings
SIGMAX_AUTH_TOKEN = os.getenv('SIGMAX_AUTH_TOKEN', None)
SIGMAX_SERVER = os.getenv('SIGMAX_SERVER', None)


#
# Zaken settings
#
# ZRC settings
# TODO: This needs to contain the correct settings for the staging environment Amsterdam.
ZRC_HOST = 'ref.tst.vng.cloud'
ZRC_PORT = '443'
ZRC_SCHEME = 'https'
ZRC_AUTH = {
    'client_id': os.getenv('ZRC_CLIENT_ID', 'mor-amsterdam-xyOyIP54BudG'),
    'secret': os.getenv('ZRC_CLIENT_SECRET', 'gdnsnNqEeDJWiDNExiSvabvOHo2KmHs9'),
    'scopes': [
        'zds.scopes.zaken.aanmaken',
        'zds.scopes.statussen.toevoegen',
        'zds.scopes.zaken.lezen',
        'zds.scopes.zaaktypes.lezen',
    ]
}
ZRC_URL = "{}://{}:{}".format(ZRC_SCHEME, ZRC_HOST, ZRC_PORT)
ZRC_ZAAKOBJECT_TYPE = 'MeldingOpenbareRuimte'

# DRC settings
# TODO: This needs to contain the correct settings for the staging environment Amsterdam.
DRC_HOST = 'ref.tst.vng.cloud'  # should be a staging domain.
DRC_PORT = '443'
DRC_SCHEME = 'https'
DRC_AUTH = {
    'client_id': os.getenv('DRC_CLIENT_ID', 'mor-amsterdam-xyOyIP54BudG'),
    'secret': os.getenv('DRC_CLIENT_SECRET', 'gdnsnNqEeDJWiDNExiSvabvOHo2KmHs9'),
    'scopes': []
}
DRC_URL = "{}://{}:{}".format(DRC_SCHEME, DRC_HOST, DRC_PORT)

# ZTC settings
# TODO: This needs to contain the correct settings for the staging environment Amsterdam.
ZTC_HOST = 'ref.tst.vng.cloud'  # should be a staging domain.
ZTC_PORT = '443'
ZTC_SCHEME = 'https'
ZTC_AUTH = {
    'client_id': os.getenv('ZTC_CLIENT_ID', 'mor-amsterdam-xyOyIP54BudG'),
    'secret': os.getenv('ZTC_CLIENT_SECRET', 'gdnsnNqEeDJWiDNExiSvabvOHo2KmHs9'),
    'scopes': [
        'zds.scopes.zaaktypes.lezen',
    ]
}
ZTC_URL = "{}://{}/ztc".format(ZTC_SCHEME, ZTC_HOST)

HOST_URL = 'https://acc.meldingen.amsterdam.nl'

ZTC_CATALOGUS_ID = '8ffb11f0-c7cc-4e35-8a64-a0639aeb8f18'
ZTC_ZAAKTYPE_ID = 'c2f952ca-298e-488c-b1be-a87f11bd5fa2'
ZTC_INFORMATIEOBJECTTYPE_ID = '5ab00303-1b58-4668-b054-595c0635596c'

ZTC_CATALOGUS_URL = '{ztc_url}/api/v1/catalogussen/{catalogus_id}'.format(
    ztc_url=ZTC_URL, catalogus_id=ZTC_CATALOGUS_ID
)
ZTC_ZAAKTYPE_URL = '{catalogus_url}/zaaktypen/{zaaktype_id}'.format(
    catalogus_url=ZTC_CATALOGUS_URL, zaaktype_id=ZTC_ZAAKTYPE_ID,
)
ZTC_INFORMATIEOBJECTTYPE_URL = '{catalogus_url}/informatieobjecttypen/{informatietype_id}'.format(
    catalogus_url=ZTC_CATALOGUS_URL, informatietype_id=ZTC_INFORMATIEOBJECTTYPE_ID,
)

RSIN_NUMBER = '002564440'
