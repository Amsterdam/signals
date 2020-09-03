import os

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

# localhost and 127.0.0.1 are allowed because the deployment process checks the health endpoint with a
# request to localhost:port
DEFAULT_ALLOWED_HOSTS = 'api.data.amsterdam.nl,acc.api.data.amsterdam.nl,localhost,127.0.0.1'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', DEFAULT_ALLOWED_HOSTS).split(',')

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
    'signals.apps.api',
    'signals.apps.users',
    'signals.apps.sigmax',
    'signals.apps.feedback',
    'signals.apps.reporting',
    'signals.apps.search',
    'signals.apps.dataset',

    'change_log',

    # Third party
    'corsheaders',
    'datapunt_api',
    'django_celery_beat',
    'django_celery_results',
    'django_extensions',
    'django_filters',
    'djcelery_email',
    'graphene_django',
    'imagekit',
    'raven.contrib.django.raven_compat',
    'rest_framework',
    'rest_framework_gis',
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
    'signals.apps.api.middleware.APIVersionHeaderMiddleware',
    'change_log.middleware.ChangeLoggerMiddleware',
]

ROOT_URLCONF = 'signals.urls'
WSGI_APPLICATION = 'signals.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'signals.context_processors.admin_feature_flags',
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
LANGUAGE_CODE = 'nl-NL'
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
if os.getenv('SWIFT_ENABLED', 'False') in ['True', 'true', '1']:
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

DWH_MEDIA_ROOT = os.getenv('DWH_MEDIA_ROOT')

# Object store - Horeca data levering
HORECA_SWIFT_AUTH_URL = os.getenv('SWIFT_AUTH_URL')
HORECA_SWIFT_USERNAME = os.getenv('HORECA_SWIFT_USERNAME')
HORECA_SWIFT_PASSWORD = os.getenv('HORECA_SWIFT_PASSWORD')
HORECA_SWIFT_TENANT_NAME = os.getenv('HORECA_SWIFT_TENANT_NAME')
HORECA_SWIFT_TENANT_ID = os.getenv('HORECA_SWIFT_TENANT_ID')
HORECA_SWIFT_REGION_NAME = os.getenv('SWIFT_REGION_NAME')
HORECA_SWIFT_CONTAINER_NAME = os.getenv('HORECA_SWIFT_CONTAINER_NAME')

# Using `HEALTH_MODEL` for health check endpoint.
HEALTH_MODEL = 'signals.Signal'

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

SIGNALS_AUTHZ = {
    'JWKS': os.getenv('PUB_JWKS', JWKS_TEST_KEY),
    'JWKS_URL': os.getenv('JWKS_URL'),
    'USER_ID_FIELD': os.getenv('USER_ID_FIELD', 'sub'),
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
CELERY_BEAT_SCHEDULE = {}

# E-mail settings for SMTP (SendGrid)
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'djcelery_email.backends.CeleryEmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
EMAIL_PORT = os.getenv('EMAIL_PORT', 465)  # 465 fort SSL 587 for TLS
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', False)
if not EMAIL_USE_TLS:
    EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', True)

# Email integration settings
EMAIL_INTEGRATIONS = dict(
    FLEX_HORECA=dict(
        RECIPIENT_LIST=[os.getenv('EMAIL_FLEX_HORECA_INTEGRATION_ADDRESS', None), ],
        APPLICABLE_RULES=dict(
            WEEKDAYS=os.getenv('EMAIL_FLEX_HORECA_WEEKDAYS', '5,6,7'),  # fri, sat, sun
            END_TIME=os.getenv('EMAIL_FLEX_HORECA_END_TIME', '04:00'),  # 04:00 o'clock
        )
    ),
    TOEZICHT_OR_NIEUW_WEST=dict(
        RECIPIENT_LIST=[os.getenv('EMAIL_TOEZICHT_OR_NIEUW_WEST_INTEGRATION_ADDRESS', None), ],
    ),
    VTH_NIEUW_WEST=dict(
        RECIPIENT_LIST=[os.getenv('EMAIL_VTH_NIEUW_WEST_INTEGRATION_ADDRESS', None), ],
    ),
)

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
            'class': 'graypy.GELFUDPHandler',
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
        'signals.apps.reporting.management.commands.dump_horeca_csv_files': {
            'level': 'DEBUG',
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
SIGMAX_SEND_FAIL_TIMEOUT_MINUTES = os.getenv('SIGMAX_SEND_FAIL_TIMEOUT_MINUTES', 60*24)  # noqa Default is 24hrs.

# SIG-884
SIGNAL_MIN_NUMBER_OF_CHILDREN = 2
SIGNAL_MAX_NUMBER_OF_CHILDREN = 3

# SIG-1017
FEEDBACK_ENV_FE_MAPPING = {
    'LOCAL': 'http://dummy_link',
    'ACCEPTANCE': 'https://acc.meldingen.amsterdam.nl',
    'PRODUCTION': 'https://meldingen.amsterdam.nl',
}

ML_TOOL_ENDPOINT = os.getenv('SIGNALS_ML_TOOL_ENDPOINT', 'https://api.data.amsterdam.nl/signals_mltool')  # noqa

# Search settings
SEARCH = {
    'PAGE_SIZE': 500,
    'CONNECTION': {
        'HOST': os.getenv('ELASTICSEARCH_HOST', 'elastic-index.service.consul:9200'),
        'INDEX': os.getenv('ELASTICSEARCH_INDEX', 'sia_signals'),
    },
}

FEATURE_FLAGS = {
    'API_FILTER_EXTRA_PROPERTIES': True,
    'API_SEARCH_ENABLED': True,
    'SEARCH_BUILD_INDEX': True,
    'API_DETERMINE_STADSDEEL_ENABLED': True,
}

API_DETERMINE_STADSDEEL_ENABLED_AREA_TYPE = 'sia-stadsdeel'

# GraphQL Settings
GRAPHENE = {
    'SCHEMA': 'signals.apps.graphql.schema.schema',
    'MIDDLEWARE': (
        'signals.apps.graphql.middleware.AuthenticationMiddleware',
    ),
    'CAMELCASE_ERRORS': True,
    'RELAY_CONNECTION_ENFORCE_FIRST_OR_LAST': True,
    'RELAY_CONNECTION_MAX_LIMIT': 50,
}

# Default pdok municipalities
DEFAULT_PDOK_MUNICIPALITIES = os.getenv(
    'DEFAULT_PDOK_MUNICIPALITIES',
    'Amsterdam,Amstelveen,Weesp',
).split(',')

# Default setting for area type
DEFAULT_SIGNAL_AREA_TYPE = os.getenv('DEFAULT_SIGNAL_AREA_TYPE', 'district')

# Logo used on first page of generated PDFs, supports SVG, PNG, and JPG in
# order of preference. Note that this logo is rescaled to 100 pixels in height.
# Note: this assumes the configured image is available through the staticfiles
# app.
API_PDF_LOGO_STATIC_FILE = os.getenv('API_PDF_LOGO_STATIC_FILE', 'api/logo-gemeente-amsterdam.svg')
