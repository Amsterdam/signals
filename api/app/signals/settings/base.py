# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2022 Gemeente Amsterdam
import os

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TRUE_VALUES = [True, 'True', 'true', '1']

# Django settings
SECRET_KEY = os.getenv('SECRET_KEY')

# Debug Logging
DEBUG = False
LOG_QUERIES = False
LOGGING_LEVEL = os.getenv('LOGGING_LEVEL', 'INFO')

# localhost and 127.0.0.1 are allowed because the deployment process checks the health endpoint with a
# request to localhost:port
DEFAULT_ALLOWED_HOSTS = 'api.data.amsterdam.nl,acc.api.data.amsterdam.nl,localhost,127.0.0.1'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', DEFAULT_ALLOWED_HOSTS).split(',')

INTERNAL_IPS = ('127.0.0.1', '0.0.0.0')

CORS_ALLOWED_ORIGINS = [origin.strip() for origin in os.getenv('CORS_ALLOWED_ORIGINS', 'null').split(',')]
CORS_ALLOW_ALL_ORIGINS = os.getenv('CORS_ALLOW_ALL_ORIGINS', True) in TRUE_VALUES

SITE_ID = 1
SITE_NAME = 'Signalen API'
SITE_DOMAIN = os.getenv('SITE_DOMAIN', 'api.data.amsterdam.nl')

ORGANIZATION_NAME = os.getenv('ORGANIZATION_NAME', 'Gemeente Amsterdam')

# The prefix of the display value of the signal ID. Defaults to 'SIG-'. This wil generate an id like SIG-123456 when
# using the `signal.get_id_display()` class method.
SIGNAL_ID_DISPLAY_PREFIX = os.getenv('SIGNAL_ID_DISPLAY_PREFIX', 'SIG-')

# Accept signals within this geographic bounding box in
# format: <lon_min>,<lat_min>,<lon_max>,<lat_max> (WS84)
# default value covers The Netherlands
BOUNDING_BOX = [float(i) for i in os.getenv('BOUNDING_BOX', '3.3,50.7,7.3,53.6').split(',')]

# Django security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Application definition
SIGNAL_APPS = [
    # Signals project
    'signals.apps.history',
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
    'signals.apps.questionnaires',
    'signals.apps.my_signals',
    'logs'
]

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
    # Third party
    'corsheaders',
    'datapunt_api',
    'django_celery_beat',
    'django_celery_results',
    'django_extensions',
    'django_filters',
    'djcelery_email',
    'markdownx',
    'raven.contrib.django.raven_compat',
    'rest_framework',
    'rest_framework_gis',
    'storages',
] + SIGNAL_APPS

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
                'signals.context_processors.settings_in_context',
            ],
            'builtins': [
                'signals.apps.email_integrations.templatetags.location',
            ],
        },
    }
]

# Database settings
DATABASE_NAME = os.getenv('DATABASE_NAME', 'signals')
DATABASE_USER = os.getenv('DATABASE_USER', 'signals')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD', 'insecure')
DATABASE_HOST = os.getenv('DATABASE_HOST_OVERRIDE')
DATABASE_PORT = os.getenv('DATABASE_PORT_OVERRIDE')


# Django cache settings
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Django security settings
SECURE_SSL_REDIRECT = True
SECURE_REDIRECT_EXEMPT = [r'^status/', ]  # Allow health checks on localhost.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True


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

AZURE_STORAGE_ENABLED = os.getenv('AZURE_STORAGE_ENABLED', False) in TRUE_VALUES
SWIFT_STORAGE_ENABLED = os.getenv('SWIFT_ENABLED', False) in TRUE_VALUES

if AZURE_STORAGE_ENABLED and SWIFT_STORAGE_ENABLED:
    raise ImproperlyConfigured('Enable AzureStorage OR SwiftStorage, not both')

if AZURE_STORAGE_ENABLED:
    # Azure Settings
    DEFAULT_FILE_STORAGE = 'storages.backends.azure_storage.AzureStorage'

    AZURE_ACCOUNT_NAME = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
    AZURE_ACCOUNT_KEY = os.getenv('AZURE_STORAGE_ACCOUNT_KEY')
    AZURE_URL_EXPIRATION_SECS = int(os.getenv('AZURE_STORAGE_URL_EXPIRATION_SECS', 30*60))

    AZURE_CONTAINER = os.getenv('AZURE_STORAGE_CONTAINER_NAME', '')  # Default container
    AZURE_CONTAINERS = {
        'main': {
            'azure_container': AZURE_CONTAINER
        },
        'datawarehouse': {
            'azure_container': os.getenv('DWH_AZURE_STORAGE_CONTAINER_NAME', AZURE_CONTAINER),
            'overwrite_files': os.getenv('DWH_AZURE_OVERWRITE_FILES', True) in TRUE_VALUES
        }
    }

elif SWIFT_STORAGE_ENABLED:
    # The default settings when using SwiftStorage to the general SIA ObjectStore
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

    SWIFT = {
        # These settings are used to create override the default Swift storage settings.
        # Useful when writing to different ObjectStores
        'datawarehouse': {
            'api_username': os.getenv('DWH_SWIFT_USERNAME'),
            'api_key': os.getenv('DWH_SWIFT_PASSWORD'),
            'tenant_name': os.getenv('DWH_SWIFT_TENANT_NAME'),
            'tenant_id': os.getenv('DWH_SWIFT_TENANT_ID'),
            'container_name': os.getenv('DWH_SWIFT_CONTAINER_NAME'),
            'auto_overwrite': os.getenv('DWH_SWIFT_AUTO_OVERWRITE', True)
        },
        'horeca': {
            'api_username': os.getenv('HORECA_SWIFT_USERNAME'),
            'api_key': os.getenv('HORECA_SWIFT_PASSWORD'),
            'tenant_name': os.getenv('HORECA_SWIFT_TENANT_NAME'),
            'tenant_id': os.getenv('HORECA_SWIFT_TENANT_ID'),
            'container_name': os.getenv('HORECA_SWIFT_CONTAINER_NAME'),
            'auto_overwrite': os.getenv('HORECA_SWIFT_AUTO_OVERWRITE', True)
        },
        'tdo': {
            'api_username': os.getenv('TDO_SWIFT_USERNAME'),
            'api_key': os.getenv('TDO_SWIFT_PASSWORD'),
            'tenant_name': os.getenv('TDO_SWIFT_TENANT_NAME'),
            'tenant_id': os.getenv('TDO_SWIFT_TENANT_ID'),
            'container_name': os.getenv('TDO_SWIFT_CONTAINER_NAME'),
            'auto_overwrite': os.getenv('TDO_SWIFT_AUTO_OVERWRITE', True)
        }
    }

# Object store - Datawarehouse (DWH)
DWH_MEDIA_ROOT = os.getenv('DWH_MEDIA_ROOT')

# Using `HEALTH_MODEL` for health check endpoint.
HEALTH_MODEL = 'signals.Signal'

SIGNALS_AUTH = {
    'JWKS': os.getenv('PUB_JWKS'),
    'JWKS_URL': os.getenv('JWKS_URL'),
    'USER_ID_FIELDS': os.getenv('USER_ID_FIELDS', 'email').split(','),
    'ALWAYS_OK': False,
}

# Celery settings
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'signals')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'insecure')
RABBITMQ_VHOST = os.getenv('RABBITMQ_VHOST', 'vhost')
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbit')

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL',
                              f'amqp://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}'
                              f'@{RABBITMQ_HOST}/{RABBITMQ_VHOST}')
CELERY_EMAIL_CHUNK_SIZE = 1
CELERY_RESULT_BACKEND = 'django-db'
CELERY_RESULT_EXTENDED = True
CELERY_TASK_RESULT_EXPIRES = 604800  # 7 days in seconds (7*24*60*60)
CELERY_TASK_ALWAYS_EAGER = os.getenv('CELERY_TASK_ALWAYS_EAGER', False) in TRUE_VALUES

# Celery Beat settings
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_BEAT_SCHEDULE = {}

# E-mail settings for SMTP (SendGrid)
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'djcelery_email.backends.CeleryEmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
EMAIL_PORT = os.getenv('EMAIL_PORT', 465)  # 465 fort SSL 587 for TLS
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', False) in TRUE_VALUES
if not EMAIL_USE_TLS:
    EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', True) in TRUE_VALUES
CELERY_EMAIL_BACKEND = os.getenv('CELERY_EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_REST_ENDPOINT = os.getenv('EMAIL_REST_ENDPOINT', None)
EMAIL_REST_ENDPOINT_TIMEOUT = os.getenv('EMAIL_REST_ENDPOINT_TIMEOUT', 5)
EMAIL_REST_ENDPOINT_CLIENT_CERT = os.getenv('EMAIL_REST_ENDPOINT_CLIENT_CERT', None)
EMAIL_REST_ENDPOINT_CLIENT_KEY = os.getenv('EMAIL_REST_ENDPOINT_CLIENT_KEY', None)

DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'Meldingen gemeente Amsterdam <noreply@meldingen.amsterdam.nl>')
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# Sentry logging
RAVEN_CONFIG = {
    'dsn': os.getenv('SENTRY_RAVEN_DSN'),
}

# Azure Application insights logging
AZURE_APPLICATION_INSIGHTS_ENABLED = os.getenv('AZURE_APPLICATION_INSIGHTS_ENABLED', False) in TRUE_VALUES
if AZURE_APPLICATION_INSIGHTS_ENABLED:
    AZURE_APPLICATION_INSIGHTS_CONNECTION_STRING = os.getenv('AZURE_APPLICATION_INSIGHTS_CONNECTION_STRING', None)

# Django REST framework settings
REST_FRAMEWORK = dict(
    PAGE_SIZE=100,
    UNAUTHENTICATED_TOKEN={},
    DEFAULT_AUTHENTICATION_CLASSES=[],
    DEFAULT_PAGINATION_CLASS='datapunt_api.pagination.HALPagination',
    DEFAULT_FILTER_BACKENDS=(
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
    DEFAULT_THROTTLE_RATES={
        'nouser': os.getenv('PUBLIC_THROTTLE_RATE', '60/hour'),
        'anon-my_signals': os.getenv('MY_SIGNALS_ANON_REPORTER_THROTTLE_RATE', '5/quarter')  # noqa:  Quarter was added only for this throttling class
    },
)

# Swagger settings
DATAPUNT_API_URL = os.getenv('DATAPUNT_API_URL', 'https://api.data.amsterdam.nl/')  # Must end with a trailing slash
SWAGGER_SETTINGS = {
    'USE_SESSION_AUTH': False,
    'SECURITY_DEFINITIONS': {
        'Signals API - Swagger': {
            'type': 'oauth2',
            'authorizationUrl': f'{DATAPUNT_API_URL}oauth2/authorize',
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

# Child settings
SIGNAL_MAX_NUMBER_OF_CHILDREN = 10

# The URL of the Frontend
FRONTEND_URL = os.getenv('FRONTEND_URL', None)

ML_TOOL_ENDPOINT = os.getenv('SIGNALS_ML_TOOL_ENDPOINT', 'https://api.data.amsterdam.nl/signals_mltool')  # noqa

# Search settings
SEARCH = {
    'PAGE_SIZE': 500,
    'CONNECTION': {
        'HOST': os.getenv('ELASTICSEARCH_HOST', 'elastic-index.service.consul:9200'),
        'INDEX': os.getenv('ELASTICSEARCH_INDEX', 'signals'),
    },
}

API_DETERMINE_STADSDEEL_ENABLED_AREA_TYPE = 'sia-stadsdeel'
API_TRANSFORM_SOURCE_BASED_ON_REPORTER_EXCEPTIONS = os.getenv(
    'API_TRANSFORM_SOURCE_BASED_ON_REPORTER_EXCEPTIONS',
    'techview@amsterdam.nl,verbeterdebuurt@amsterdam.nl,hnw@amsterdam.nl,webcare@amsterdam.nl,qubz@amsterdam.nl'
).split(',')
API_TRANSFORM_SOURCE_BASED_ON_REPORTER_DOMAIN_EXTENSIONS = os.getenv(
    'API_TRANSFORM_SOURCE_BASED_ON_REPORTER_DOMAIN_EXTENSIONS',
    '@amsterdam.nl',
)
API_TRANSFORM_SOURCE_BASED_ON_REPORTER_SOURCE = os.getenv(
    'API_TRANSFORM_SOURCE_BASED_ON_REPORTER_SOURCE', 'Interne melding'
)
API_TRANSFORM_SOURCE_OF_CHILD_SIGNAL_TO = os.getenv('API_TRANSFORM_SOURCE_OF_CHILD_SIGNAL_TO', 'Interne melding')

# Default pdok municipalities
DEFAULT_PDOK_MUNICIPALITIES = os.getenv('DEFAULT_PDOK_MUNICIPALITIES',
                                        'Amsterdam,Amstelveen,Weesp,Ouder-Amstel').split(',')

# use dynamic map server for pdf, empty by default
# example servers
# 'https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/standaard/EPSG:28992/{z}/{x}/{y}.png'
# 'https://a.tile.openstreetmap.org/{zoom}/{x}/{y}.png'
DEFAULT_MAP_TILE_SERVER = os.getenv('DEFAULT_MAP_TILE_SERVER', '')

# Default setting for area type
DEFAULT_SIGNAL_AREA_TYPE = os.getenv('DEFAULT_SIGNAL_AREA_TYPE', 'district')

# Logo used on first page of generated PDFs, supports SVG, PNG, and JPG in
# order of preference. Note that this logo is rescaled to 100 pixels in height.
# Note: this assumes the configured image is available through the staticfiles
# app.
API_PDF_LOGO_STATIC_FILE = os.getenv('API_PDF_LOGO_STATIC_FILE', 'api/logo-gemeente-amsterdam.svg')

# Large images are resized to max dimension of `API_PDF_RESIZE_IMAGES_TO`
# along the largest side, aspect ratio is maintained.
API_PDF_RESIZE_IMAGES_TO = 800

# Maximum size for attachments
API_MAX_UPLOAD_SIZE = os.getenv('API_MAX_UPLOAD_SIZE', 20*1024*1024)  # 20MB = 20*1024*1024

# Enable public map geo endpoint
ENABLE_PUBLIC_GEO_SIGNAL_ENDPOINT = os.getenv('ENABLE_PUBLIC_GEO_SIGNAL_ENDPOINT', False) in TRUE_VALUES

# Allow 'invalid' address as unverified
ALLOW_INVALID_ADDRESS_AS_UNVERIFIED = os.getenv('ALLOW_INVALID_ADDRESS_AS_UNVERIFIED', False) in TRUE_VALUES

# Max instances we allow per Category/State combination
STATUS_MESSAGE_TEMPLATE_MAX_INSTANCES = os.getenv('STATUS_MESSAGE_TEMPLATE_MAX_INSTANCES', 20)

MARKDOWNX_MARKDOWNIFY_FUNCTION = 'signals.apps.email_integrations.utils.markdownx_md'  # noqa Renders markdown as HTML using Mistune
MARKDOWNX_URLS_PATH = '/signals/markdownx/markdownify/'  # The url path that Signals has for markdownx
