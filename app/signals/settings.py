# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2024 Gemeente Amsterdam
import json
import os
from typing import Any, Callable

# Export modules to Azure Application Insights
from azure.monitor.opentelemetry.exporter import AzureMonitorLogExporter, AzureMonitorTraceExporter
# Opentelemetry modules needed for logging and tracing
from opentelemetry import trace
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from signals import __version__

BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))

TRUE_VALUES: list[bool | str] = [True, 'True', 'true', '1']

# Django settings
SECRET_KEY: str | None = os.getenv('SECRET_KEY')

# Debug Logging
DEBUG: bool = os.getenv('DJANGO_DEBUG', False) in TRUE_VALUES
LOGGING_LEVEL: str = os.getenv('LOGGING_LEVEL', 'INFO')

# localhost and 127.0.0.1 are allowed because the deployment process checks the health endpoint with a
# request to localhost:port
DEFAULT_ALLOWED_HOSTS: str = 'api.data.amsterdam.nl,acc.api.data.amsterdam.nl,localhost,127.0.0.1'
ALLOWED_HOSTS: list[str] = os.getenv('ALLOWED_HOSTS', DEFAULT_ALLOWED_HOSTS).split(',')

INTERNAL_IPS: tuple[str, str] = (
    '127.0.0.1',
    '0.0.0.0',
)

CORS_ALLOWED_ORIGINS: list[str] = [
    origin.strip()
    for origin in os.getenv('CORS_ALLOWED_ORIGINS', 'null').split(',')
]
CORS_ALLOW_ALL_ORIGINS: bool = os.getenv('CORS_ALLOW_ALL_ORIGINS', True) in TRUE_VALUES
CORS_EXPOSE_HEADERS: list[str] = [
    'Link',  # Added for the geography endpoints
    'X-API-Version',  # General API version
    'X-Total-Count',  # Added for the geography endpoints
]

ORGANIZATION_NAME: str = os.getenv('ORGANIZATION_NAME', 'Gemeente Amsterdam')

# The prefix of the display value of the signal ID. Defaults to 'SIG-'. This wil generate an id like SIG-123456 when
# using the `signal.get_id_display()` class method.
SIGNAL_ID_DISPLAY_PREFIX: str = os.getenv('SIGNAL_ID_DISPLAY_PREFIX', 'SIG-')

# Accept signals within this geographic bounding box in
# format: <lon_min>,<lat_min>,<lon_max>,<lat_max> (WS84)
# default value covers The Netherlands
BOUNDING_BOX: list[float] = [float(i) for i in os.getenv('BOUNDING_BOX', '3.3,50.7,7.3,53.6').split(',')]

# Django's security settings
SECURE_BROWSER_XSS_FILTER: bool = True
SECURE_CONTENT_TYPE_NOSNIFF: bool = True
X_FRAME_OPTIONS: str = 'DENY'

# Application definition
SIGNAL_APPS: list[str] = [
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
    'signals.apps.classification',
    'signals.apps.relations',
]

INSTALLED_APPS: list[str] = [
    # Django
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'django.contrib.messages',
    'django.contrib.sessions',
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
    'rest_framework',
    'rest_framework_gis',
    'storages',
    'mozilla_django_oidc',
    'silk',
    'drf_spectacular',
    'drf_spectacular_sidecar',
] + SIGNAL_APPS

MIDDLEWARE: list[str] = [
    'corsheaders.middleware.CorsMiddleware',
    'signals.apps.api.middleware.MaintenanceModeMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'signals.apps.api.middleware.APIVersionHeaderMiddleware',
]

# Enable session cookies when authenticating using the bearer token
SESSION_SUPPORT_ON_TOKEN_AUTHENTICATION: bool = \
    os.getenv('SESSION_SUPPORT_ON_TOKEN_AUTHENTICATION', False) in TRUE_VALUES
if SESSION_SUPPORT_ON_TOKEN_AUTHENTICATION:
    MIDDLEWARE.append('signals.apps.api.middleware.SessionLoginMiddleware')
    SESSION_EXPIRE_AT_BROWSER_CLOSE: bool = True
    SESSION_COOKIE_DOMAIN: str | None = os.getenv('SESSION_COOKIE_DOMAIN', None)
    SESSION_COOKIE_SAMESITE: str = 'None'
    CORS_ALLOW_CREDENTIALS: bool = True


# Setup django-silk
def is_super_user(user) -> bool:
    return user.is_superuser


SILK_ENABLED: bool = os.getenv('SILK_ENABLED') in TRUE_VALUES
if SILK_ENABLED:
    MIDDLEWARE.append('silk.middleware.SilkyMiddleware')
    SILKY_META: bool = True

    SILK_PROFILING_ENABLED: bool = os.getenv('SILK_PROFILING_ENABLED') in TRUE_VALUES
    if SILK_PROFILING_ENABLED:
        SILKY_PYTHON_PROFILER: bool = True
        SILKY_PYTHON_PROFILER_BINARY: bool = True

    # If SILK_AUTHENTICATION_ENABLED is enabled you need to log in to Django admin first as a superuser
    SILK_AUTHENTICATION_ENABLED: bool = os.getenv('SILK_AUTHENTICATION_ENABLED') in TRUE_VALUES
    if SILK_AUTHENTICATION_ENABLED:
        SILKY_AUTHENTICATION: bool = True
        SILKY_AUTHORISATION: bool = True
        SILKY_PERMISSIONS: Callable[..., bool] = is_super_user

OIDC_RP_CLIENT_ID: str | None = os.getenv('OIDC_RP_CLIENT_ID')
OIDC_RP_CLIENT_SECRET: str | None = os.getenv('OIDC_RP_CLIENT_SECRET')
OIDC_OP_AUTHORIZATION_ENDPOINT: str | None = os.getenv('OIDC_OP_AUTHORIZATION_ENDPOINT')
OIDC_OP_TOKEN_ENDPOINT: str | None = os.getenv('OIDC_OP_TOKEN_ENDPOINT')
OIDC_OP_USER_ENDPOINT: str | None = os.getenv('OIDC_OP_USER_ENDPOINT')
OIDC_OP_JWKS_ENDPOINT: str | None = os.getenv('OIDC_OP_JWKS_ENDPOINT')
if OIDC_OP_JWKS_ENDPOINT is not None:
    OIDC_RP_SIGN_ALGO: str = 'RS256'
OIDC_CREATE_USER: bool = False
OIDC_OP_ISSUER: str | None = os.getenv("OIDC_OP_ISSUER")
OIDC_TRUSTED_AUDIENCES: list[str] = json.loads(os.getenv("OIDC_TRUSTED_AUDIENCES", '[]'))
OIDC_VERIFY_AUDIENCE: bool = os.getenv('OIDC_VERIFY_AUDIENCE', True) in TRUE_VALUES
OIDC_USE_NONCE: bool = os.getenv('OIDC_USE_NONCE', True) in TRUE_VALUES

PUB_JWKS: str | None = os.getenv('PUB_JWKS')

NLTK_DOWNLOAD_DIR: str | None = os.getenv('NLTK_DOWNLOAD_DIR')

AUTHENTICATION_BACKENDS: list[str] = [
    'signals.admin.oidc.backends.AuthenticationBackend',
]

ADMIN_ENABLE_LOCAL_LOGIN: bool = os.getenv('ADMIN_ENABLE_LOCAL_LOGIN', False) in TRUE_VALUES
if ADMIN_ENABLE_LOCAL_LOGIN:
    AUTHENTICATION_BACKENDS.append("django.contrib.auth.backends.ModelBackend")

LOGIN_REDIRECT_URL: str = '/signals/admin/'
LOGIN_REDIRECT_URL_FAILURE: str = '/signals/oidc/login_failure/'
LOGOUT_REDIRECT_URL: str = '/signals/admin/'

ROOT_URLCONF: str = 'signals.urls'
WSGI_APPLICATION: str = 'signals.wsgi.application'

TEMPLATES: list[dict[str, str | bool | list[str] | dict[str, str | list[str]]]] = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
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
DATABASES: dict[str, dict[str, str | int | None]] = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('DATABASE_NAME', 'signals'),
        'USER': os.getenv('DATABASE_USER', 'signals'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', 'insecure'),
        'HOST': os.getenv('DATABASE_HOST_OVERRIDE'),
        'PORT': os.getenv('DATABASE_PORT_OVERRIDE', '5432')
    },
}

# Django cache settings
CACHES: dict[str, dict[str, str | int]] = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'signals_cache',
        'TIMEOUT': os.getenv('CACHE_TIMEOUT', 3900),
    }
}

# Django security settings
SECURE_SSL_REDIRECT: bool = os.getenv('SECURE_SSL_REDIRECT', True) in TRUE_VALUES
SECURE_REDIRECT_EXEMPT: list[str] = [r'^status/', ]  # Allow health checks on localhost.
SECURE_PROXY_SSL_HEADER: tuple[str, str] = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE: bool = os.getenv('SESSION_COOKIE_SECURE', True) in TRUE_VALUES
CSRF_COOKIE_SECURE: bool = os.getenv('CSRF_COOKIE_SECURE', True) in TRUE_VALUES


# Internationalization
LANGUAGE_CODE: str = 'nl-NL'
TIME_ZONE: str = 'Europe/Amsterdam'
USE_I18N: bool = True
USE_TZ: bool = True
DATETIME_FORMAT: str = 'l d-m-Y, H:i'  # e.g. "Donderdag 06-09-2018, 13:56"

# Static files (CSS, JavaScript, Images) and media files
STATIC_URL: str = '/signals/static/'
STATIC_ROOT: str = os.path.join(os.path.dirname(BASE_DIR), 'static')
MEDIA_URL: str = '/signals/media/'
MEDIA_ROOT: str = os.path.join(os.path.dirname(BASE_DIR), 'media')

PROTECTED_FILE_SYSTEM_STORAGE: bool = os.getenv('PROTECTED_FILE_SYSTEM_STORAGE', False) in TRUE_VALUES
if PROTECTED_FILE_SYSTEM_STORAGE:
    DEFAULT_FILE_STORAGE: str = 'signals.apps.media.storages.ProtectedFileSystemStorage'

AZURE_STORAGE_ENABLED: bool = os.getenv('AZURE_STORAGE_ENABLED', False) in TRUE_VALUES
if AZURE_STORAGE_ENABLED:
    # Azure Settings
    DEFAULT_FILE_STORAGE: str = 'storages.backends.azure_storage.AzureStorage'

    AZURE_ACCOUNT_NAME: str | None = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
    AZURE_ACCOUNT_KEY: str | None = os.getenv('AZURE_STORAGE_ACCOUNT_KEY')
    AZURE_URL_EXPIRATION_SECS = int(os.getenv('AZURE_STORAGE_URL_EXPIRATION_SECS', 30*60))

    AZURE_CONTAINER: str = os.getenv('AZURE_STORAGE_CONTAINER_NAME', '')  # Default container
    AZURE_CONTAINERS: dict[str, dict[str, str | bool]] = {
        'main': {
            'azure_container': AZURE_CONTAINER
        },
        'datawarehouse': {
            'azure_container': os.getenv('DWH_AZURE_STORAGE_CONTAINER_NAME', AZURE_CONTAINER),
            'overwrite_files': os.getenv('DWH_AZURE_OVERWRITE_FILES', True) in TRUE_VALUES
        }
    }

    AZURE_CUSTOM_DOMAIN: str | None = os.getenv('AZURE_STORAGE_CUSTOM_DOMAIN', None)

# Save files using system's standard umask. This is required for network mounts like
# Azure Files as they do not implement a full-fledged permission system.
# See https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-FILE_UPLOAD_PERMISSIONS
FILE_UPLOAD_PERMISSIONS: None = None

# Object store - Datawarehouse (DWH)
DWH_MEDIA_ROOT: str | None = os.getenv('DWH_MEDIA_ROOT')

SIGNALS_AUTH: dict[str, str | bool | list[str] | None] = {
    'USER_ID_FIELDS': os.getenv('USER_ID_FIELDS', 'email').split(','),
    'ALWAYS_OK': os.getenv('SIGNALS_AUTH_ALWAYS_OK', False) in TRUE_VALUES,
}

# Celery settings
RABBITMQ_USER: str = os.getenv('RABBITMQ_USER', 'signals')
RABBITMQ_PASSWORD: str = os.getenv('RABBITMQ_PASSWORD', 'insecure')
RABBITMQ_VHOST: str = os.getenv('RABBITMQ_VHOST', 'vhost')
RABBITMQ_HOST: str = os.getenv('RABBITMQ_HOST', 'rabbit')

CELERY_BROKER_URL: str = os.getenv('CELERY_BROKER_URL',
                                   f'amqp://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}'
                                   f'@{RABBITMQ_HOST}/{RABBITMQ_VHOST}')
CELERY_RESULT_BACKEND: str = 'django-db'
CELERY_RESULT_EXTENDED: bool = True
CELERY_TASK_RESULT_EXPIRES: int = 604800  # 7 days in seconds (7*24*60*60)
CELERY_TASK_ALWAYS_EAGER: bool = os.getenv('CELERY_TASK_ALWAYS_EAGER', False) in TRUE_VALUES
CELERY_TASK_DEFAULT_PRIORITY = 5  # Make sure that all task are scheduled with a default priority of '5'

# Celery Beat settings
CELERY_BEAT_SCHEDULER: str = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_BEAT_SCHEDULE: dict[str, dict[str, Any]] = {}

# E-mail settings for SMTP (SendGrid)
EMAIL_BACKEND: str = os.getenv('EMAIL_BACKEND', 'djcelery_email.backends.CeleryEmailBackend')
EMAIL_HOST: str | None = os.getenv('EMAIL_HOST')
EMAIL_HOST_USER: str | None = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD: str | None = os.getenv('EMAIL_HOST_PASSWORD')
EMAIL_PORT: int = int(os.getenv('EMAIL_PORT', 465))  # 465 for SSL 587 for TLS
EMAIL_TIMEOUT: int = int(os.getenv('EMAIL_TIMEOUT', 5))
EMAIL_USE_TLS: bool = os.getenv('EMAIL_USE_TLS', False) in TRUE_VALUES
if not EMAIL_USE_TLS:
    EMAIL_USE_SSL: bool = os.getenv('EMAIL_USE_SSL', True) in TRUE_VALUES

CELERY_EMAIL_BACKEND: str = os.getenv('CELERY_EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_REST_ENDPOINT: str | None = os.getenv('EMAIL_REST_ENDPOINT', None)
EMAIL_REST_ENDPOINT_TIMEOUT: str | int = os.getenv('EMAIL_REST_ENDPOINT_TIMEOUT', 5)
EMAIL_REST_ENDPOINT_CLIENT_CERT: str | None = os.getenv('EMAIL_REST_ENDPOINT_CLIENT_CERT', None)
EMAIL_REST_ENDPOINT_CLIENT_KEY: str | None = os.getenv('EMAIL_REST_ENDPOINT_CLIENT_KEY', None)
EMAIL_REST_ENDPOINT_CA_BUNDLE: str | None = os.getenv('EMAIL_REST_ENDPOINT_CA_BUNDLE', None)

O365_ACTUALLY_SEND_IN_DEBUG: bool = os.getenv('O365_ACTUALLY_SEND_IN_DEBUG', False) in TRUE_VALUES
O365_MAIL_SAVE_TO_SENT: bool = os.getenv('O365_MAIL_SAVE_TO_SENT', False) in TRUE_VALUES
O365_MAIL_CLIENT_ID: str | None = os.getenv('O365_MAIL_CLIENT_ID', None)
O365_MAIL_CLIENT_SECRET: str | None = os.getenv('O365_MAIL_CLIENT_SECRET', None)
O365_MAIL_TENANT_ID: str | None = os.getenv('O365_MAIL_TENANT_ID', None)
O365_MAIL_ACCOUNT_KWARGS: dict[str, str] = {
    'token_backend': 'O365.utils.token.EnvTokenBackend'
}

O365_MAIL_RESOURCE: str | None = os.getenv('O365_MAIL_RESOURCE')
if O365_MAIL_RESOURCE is not None:
    O365_MAIL_MAILBOX_KWARGS: dict[str, str] = {
        'resource': O365_MAIL_RESOURCE
    }

DEFAULT_FROM_EMAIL: str = os.getenv('DEFAULT_FROM_EMAIL',
                                    'Meldingen gemeente Amsterdam <noreply@meldingen.amsterdam.nl>')
DEFAULT_AUTO_FIELD: str = 'django.db.models.AutoField'

CELERY_EMAIL_CHUNK_SIZE: int = 1
CELERY_EMAIL_TASK_CONFIG: dict[str, bool | str | int] = {
    'ignore_result': False,
}
celery_email_task_config_max_retries = os.getenv('CELERY_EMAIL_TASK_CONFIG_MAX_RETRIES')
if celery_email_task_config_max_retries is not None:
    CELERY_EMAIL_TASK_CONFIG['max_retries'] = int(celery_email_task_config_max_retries)

celery_email_task_config_default_retry_delay = os.getenv('CELERY_EMAIL_TASK_CONFIG_DEFAULT_RETRY_DELAY')
if celery_email_task_config_default_retry_delay is not None:
    CELERY_EMAIL_TASK_CONFIG['default_retry_delay'] = int(celery_email_task_config_default_retry_delay)

AZURE_APPLICATION_INSIGHTS_ENABLED: bool = os.getenv('AZURE_APPLICATION_INSIGHTS_ENABLED', False) in TRUE_VALUES

# Azure Application insights logging
if AZURE_APPLICATION_INSIGHTS_ENABLED:
    AZURE_APPLICATION_INSIGHTS_CONNECTION_STRING: str | None = os.getenv('AZURE_APPLICATION_INSIGHTS_CONNECTION_STRING',
                                                                         None)

# Django REST framework settings
REST_FRAMEWORK: dict[str, int | str | list[str] | dict[str, str]] = dict(
    PAGE_SIZE=100,
    UNAUTHENTICATED_TOKEN={},
    DEFAULT_SCHEMA_CLASS='signals.schema.SIGAutoSchema',
    DEFAULT_AUTHENTICATION_CLASSES=[],
    DEFAULT_PAGINATION_CLASS='signals.apps.api.generics.pagination.HALPagination',
    DEFAULT_FILTER_BACKENDS=[
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
    DEFAULT_THROTTLE_RATES={
        'nouser': os.getenv('PUBLIC_THROTTLE_RATE', '60/hour'),
        'anon-my_signals': os.getenv('MY_SIGNALS_ANON_REPORTER_THROTTLE_RATE', '5/quarter')  # noqa:  Quarter was added only for this throttling class
    },
    EXCEPTION_HANDLER='signals.apps.api.views.api_exception_handler',
)

# Sigmax settings
SIGMAX_AUTH_TOKEN: str | None = os.getenv('SIGMAX_AUTH_TOKEN', None)
SIGMAX_SERVER: str | None = os.getenv('SIGMAX_SERVER', None)
SIGMAX_CA_BUNDLE: str | None = os.getenv('SIGMAX_CA_BUNDLE', None)
SIGMAX_CLIENT_CERT: str | None = os.getenv('SIGMAX_CLIENT_CERT', None)
SIGMAX_CLIENT_KEY: str | None = os.getenv('SIGMAX_CLIENT_KEY', None)
SIGMAX_SEND_FAIL_TIMEOUT_MINUTES: str | int = os.getenv('SIGMAX_SEND_FAIL_TIMEOUT_MINUTES', 60*24)  # noqa Default is 24hrs.
SIGMAX_END_STATE_IS_AFGEHANDELD: bool = os.getenv('SIGMAX_END_STATE_IS_AFGEHANDELD', False) in TRUE_VALUES
SIGMAX_END_STATE_IS_AFGEHANDELD_STATUS_TEXT: str = os.getenv('SIGMAX_END_STATE_IS_AFGEHANDELD_STATUS_TEXT', 'We hebben uw melding opgelost. Bedankt voor het doorgeven!')

SIGMAX_TRANSFORM_DESCRIPTION_BASED_ON_SOURCE: str | None = os.getenv(
    'SIGMAX_TRANSFORM_DESCRIPTION_BASED_ON_SOURCE', None
)  # If specific source is given the text Signalering will be added to the description to SIGMAX

# Child settings
SIGNAL_MAX_NUMBER_OF_CHILDREN: int = 10

# The URL of the Frontend
FRONTEND_URL: str | None = os.getenv('FRONTEND_URL', None)
BACKEND_URL: str | None = os.getenv('BACKEND_URL', 'http://localhost:8000')

ML_TOOL_ENDPOINT: str = os.getenv('SIGNALS_ML_TOOL_ENDPOINT', 'https://api.data.amsterdam.nl/signals_mltool')  # noqa

# Search settings
SEARCH: dict[str, int | dict[str, str]] = {
    'PAGE_SIZE': 500,
    'CONNECTION': {
        'HOST': os.getenv('ELASTICSEARCH_HOST', 'elastic-index.service.consul:9200'),
        'INDEX': os.getenv('ELASTICSEARCH_INDEX', 'signals'),
        'STATUS_MESSAGE_INDEX': os.getenv('ELASTICSEARCH_STATUS_MESSAGE_INDEX', 'status_messages'),
    },
    'TIMEOUT': int(os.getenv('ELASTICSEARCH_TIMEOUT', 10)),
}

API_DETERMINE_STADSDEEL_ENABLED_AREA_TYPE: str = 'sia-stadsdeel'
API_TRANSFORM_SOURCE_BASED_ON_REPORTER_EXCEPTIONS: list[str] = os.getenv(
    'API_TRANSFORM_SOURCE_BASED_ON_REPORTER_EXCEPTIONS',
    'techview@amsterdam.nl,verbeterdebuurt@amsterdam.nl,hnw@amsterdam.nl,webcare@amsterdam.nl,qubz@amsterdam.nl'
).split(',')
API_TRANSFORM_SOURCE_BASED_ON_REPORTER_DOMAIN_EXTENSIONS: str = os.getenv(
    'API_TRANSFORM_SOURCE_BASED_ON_REPORTER_DOMAIN_EXTENSIONS',
    '@amsterdam.nl',
)
API_TRANSFORM_SOURCE_BASED_ON_REPORTER_SOURCE: str = os.getenv(
    'API_TRANSFORM_SOURCE_BASED_ON_REPORTER_SOURCE', 'Interne melding'
)
API_TRANSFORM_SOURCE_OF_CHILD_SIGNAL_TO: str = os.getenv('API_TRANSFORM_SOURCE_OF_CHILD_SIGNAL_TO', 'Interne melding')

# Default pdok municipalities
PDOK_LOCATIESERVER_SUGGEST_ENDPOINT: str = os.getenv('PDOK_LOCATIESERVER_SUGGEST_ENDPOINT',
                                                     'https://api.pdok.nl/bzk/locatieserver/search/v3_1/suggest')
DEFAULT_PDOK_MUNICIPALITIES: list[str] = os.getenv('DEFAULT_PDOK_MUNICIPALITIES',
                                                   'Amsterdam,Amstelveen,Weesp,Ouder-Amstel').split(',')

# use dynamic map server for pdf, empty by default
# example servers
# 'https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/standaard/EPSG:28992/{z}/{x}/{y}.png'
# 'https://a.tile.openstreetmap.org/{zoom}/{x}/{y}.png'
DEFAULT_MAP_TILE_SERVER: str = os.getenv('DEFAULT_MAP_TILE_SERVER', '')

# Default setting for area type
DEFAULT_SIGNAL_AREA_TYPE: str = os.getenv('DEFAULT_SIGNAL_AREA_TYPE', 'district')

# Logo used on first page of generated PDFs, supports SVG, PNG, and JPG in
# order of preference. Note that this logo is rescaled to 100 pixels in height.
# Note: this assumes the configured image is available through the staticfiles
# app.
API_PDF_LOGO_STATIC_FILE: str = os.getenv('API_PDF_LOGO_STATIC_FILE', 'api/logo-gemeente-amsterdam.svg')

# Large images are resized to max dimension of `API_PDF_RESIZE_IMAGES_TO`
# along the largest side, aspect ratio is maintained.
API_PDF_RESIZE_IMAGES_TO: int = 800

# Maximum size for attachments
API_MAX_UPLOAD_SIZE: int = int(os.getenv('API_MAX_UPLOAD_SIZE', '20971520'))  # 20MB

# Enable public map geo endpoint
ENABLE_PUBLIC_GEO_SIGNAL_ENDPOINT: bool = os.getenv('ENABLE_PUBLIC_GEO_SIGNAL_ENDPOINT', False) in TRUE_VALUES

# Allow 'invalid' address as unverified
ALLOW_INVALID_ADDRESS_AS_UNVERIFIED: bool = os.getenv('ALLOW_INVALID_ADDRESS_AS_UNVERIFIED', False) in TRUE_VALUES

# Max instances we allow per Category/State combination
STATUS_MESSAGE_TEMPLATE_MAX_INSTANCES: str | int = os.getenv('STATUS_MESSAGE_TEMPLATE_MAX_INSTANCES', 20)

MARKDOWNX_MARKDOWNIFY_FUNCTION: str = 'signals.apps.email_integrations.utils.markdownx_md'  # noqa Renders markdown as HTML using Mistune
MARKDOWNX_URLS_PATH: str = '/signals/markdownx/markdownify/'  # The url path that Signals has for markdownx

# DRF Spectacular settings
SPECTACULAR_SETTINGS: dict[str, str | float | int | bool | list[str]] = {
    'TITLE': 'Signalen API',
    'DESCRIPTION': 'One of the tasks of a municipality is to maintain public spaces. When citizens have '
                   'complaints about public spaces they can leave these complaints with the municipality. '
                   'Signalen (SIG) receives these complaints and is used to track progress towards their '
                   'resolution. SIG provides an API that is used both by the SIG frontend and external '
                   'systems that integrate with SIG.',
    'VERSION': __version__,
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_DIST': 'SIDECAR',
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'GENERIC_ADDITIONAL_PROPERTIES': True,
    'AUTHENTICATION_WHITELIST': [
        'signals.auth.backend.JWTAuthBackend',
        'signals.apps.my_signals.rest_framework.authentication.MySignalsTokenAuthentication'
    ],
}

EMAIL_VERIFICATION_TOKEN_HOURS_VALID: float = float(os.getenv('EMAIL_VERIFICATION_TOKEN_HOURS_VALID', 24))


# Signals API settings
SIGNAL_API_CONTEXT_GEOGRAPHY_RADIUS: int = int(os.getenv(
    'SIGNAL_API_CONTEXT_GEOGRAPHY_RADIUS', '50'
))  # Radius in meters

SIGNAL_API_CONTEXT_GEOGRAPHY_CREATED_DELTA_WEEKS: int = int(os.getenv(
    'SIGNAL_API_CONTEXT_GEOGRAPHY_CREATED_DELTA_WEEKS', '12'
))  # Created gte X weeks ago

SIGNALS_API_GEO_PAGINATE_BY: int = int(os.getenv(
    'SIGNALS_API_GEO_PAGINATE_BY', '4000'
))

TEST_LOGIN: str = os.getenv('TEST_LOGIN', 'signals.admin@example.com')

# Feature Flags
FEATURE_FLAGS: dict[str, bool] = {
    'API_DETERMINE_STADSDEEL_ENABLED': os.getenv('API_DETERMINE_STADSDEEL_ENABLED', True) in TRUE_VALUES,
    'API_TRANSFORM_SOURCE_BASED_ON_REPORTER': os.getenv('API_TRANSFORM_SOURCE_BASED_ON_REPORTER', True) in TRUE_VALUES,

    'AUTOMATICALLY_CREATE_CHILD_SIGNALS_PER_CONTAINER': os.getenv('AUTOMATICALLY_CREATE_CHILD_SIGNALS_PER_CONTAINER', False) in TRUE_VALUES,  # noqa
    'AUTOMATICALLY_CREATE_CHILD_SIGNALS_PER_EIKENPROCESSIERUPS_TREE': os.getenv('AUTOMATICALLY_CREATE_CHILD_SIGNALS_PER_EIKENPROCESSIERUPS_TREE', False) in TRUE_VALUES,  # noqa

    'API_USE_QUESTIONNAIRES_APP_FOR_FEEDBACK': os.getenv('API_USE_QUESTIONNAIRES_APP_FOR_FEEDBACK', False) in TRUE_VALUES,  # noqa

    # Enable/disable system mail for Feedback Received
    'SYSTEM_MAIL_FEEDBACK_RECEIVED_ENABLED': os.getenv('SYSTEM_MAIL_FEEDBACK_RECEIVED_ENABLED', False) in TRUE_VALUES,  # noqa

    # Enable/disable status mail for Handled after negative feedback
    'REPORTER_MAIL_HANDLED_NEGATIVE_CONTACT_ENABLED': os.getenv('REPORTER_MAIL_HANDLED_NEGATIVE_CONTACT_ENABLED', False) in TRUE_VALUES, # noqa

    # Enable/disable only mail when Feedback allows_contact is True
    'REPORTER_MAIL_CONTACT_FEEDBACK_ALLOWS_CONTACT_ENABLED': os.getenv('REPORTER_MAIL_CONTACT_FEEDBACK_ALLOWS_CONTACT_ENABLED', True) in TRUE_VALUES, # noqa

    # Enable/disable the deletion of signals in a certain state for a certain amount of time
    'DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED': os.getenv('DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED', False) in TRUE_VALUES,  # noqa

    # Enable/Disable the "my signals" endpoint/flows (Disabled by default)
    'MY_SIGNALS_ENABLED': os.getenv('MY_SIGNALS_ENABLED', False) in TRUE_VALUES,

    # Run routing expressions again when updating signal subcategory or location
    'DSL_RUN_ROUTING_EXPRESSIONS_ON_UPDATES': os.getenv('DSL_RUN_ROUTING_EXPRESSIONS_ON_UPDATES', False) in TRUE_VALUES,
}

# Per default log to console
LOGGING_HANDLERS: dict[str, dict[str, Any]] = {
    'console': {
        'class': 'logging.StreamHandler',
    },
}
LOGGER_HANDLERS = ['console', ]

MONITOR_SERVICE_NAME = 'meldingen-api'
resource: Resource = Resource.create({"service.name": MONITOR_SERVICE_NAME})

tracer_provider: TracerProvider = TracerProvider(resource=resource)
trace.set_tracer_provider(tracer_provider)


# As required, the user id and name is attached to each request that is recorded as a span
def response_hook(span, request, response):
    if (
        span and
        span.is_recording() and
        hasattr(request, 'user') and
        request.user is not None and
        hasattr(request.user, 'is_authenticated') and
        request.user.is_authenticated is True
    ):
        span.set_attributes({
            'user_id': request.user.id,
            'username': request.user.username
        })


# Logs and traces will be exported to Azure Application Insights
if AZURE_APPLICATION_INSIGHTS_ENABLED and AZURE_APPLICATION_INSIGHTS_CONNECTION_STRING:

    # Enable exporting of traces
    span_exporter: AzureMonitorTraceExporter = AzureMonitorTraceExporter(
        connection_string=AZURE_APPLICATION_INSIGHTS_CONNECTION_STRING
    )
    tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter=span_exporter))

    # Enable exporting of logs
    log_exporter: AzureMonitorLogExporter = AzureMonitorLogExporter(
        connection_string=AZURE_APPLICATION_INSIGHTS_CONNECTION_STRING
    )
    logger_provider: LoggerProvider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter, schedule_delay_millis=3000))

    # Custom logging handler to attach to logging config
    class AzureLoggingHandler(LoggingHandler):
        def __init__(self):
            super().__init__(logger_provider=logger_provider)

    LOGGING_HANDLERS.update({
        'azure': {
            '()': AzureLoggingHandler,
            'formatter': 'elaborate',
            'level': 'INFO'
        }
    })

    LOGGER_HANDLERS.append('azure')

# Instrument Django and the postgres database
# This will attach logs from the logger module to traces
Psycopg2Instrumentor().instrument(tracer_provider=tracer_provider, skip_dep_check=True)
DjangoInstrumentor().instrument(tracer_provider=tracer_provider, response_hook=response_hook)

LOGGING: dict[str, Any] = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'elaborate': {
            'format': '{levelname} {module}.{filename} {message}',
            'style': '{'
        }
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': LOGGING_HANDLERS,
    'loggers': {
        '': {
            'level': LOGGING_LEVEL,
            'handlers': LOGGER_HANDLERS,
            'propagate': False,
        },
        'django.utils.autoreload': {
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

if AZURE_APPLICATION_INSIGHTS_ENABLED:
    LOGGING['loggers'].update({
        "azure.monitor.opentelemetry.exporter.export._base": {
            "handlers": LOGGER_HANDLERS,
            "level": "ERROR",  # Set to INFO to log what is being logged to Azure
        },
        "azure.core.pipeline.policies.http_logging_policy": {
            "handlers": LOGGER_HANDLERS,
            "level": "ERROR",  # Set to INFO to log what is being logged to Azure
        },
    })
else:
    # When in debug mode without Azure Insights, queries will be logged to console
    LOGGING['loggers'].update({
        'django.db.backends': {
            'handlers': LOGGER_HANDLERS,
            'level': LOGGING_LEVEL,
            'propagate': False,
            'filters': ['require_debug_true', ],
        }
    })
