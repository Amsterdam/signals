import os

from signals.settings_common import *  # noqa F403
from signals.settings_common import INSTALLED_APPS

from signals.settings_databases import (
    LocationKey,
    get_docker_host,
    get_database_key,
    OVERRIDE_HOST_ENV_VAR,
    OVERRIDE_PORT_ENV_VAR,
)

# Application definition

INSTALLED_APPS += ["drf_yasg", "storages", "signals"]

ROOT_URLCONF = "signals.urls"

WSGI_APPLICATION = "signals.wsgi.application"


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
        "PORT": "5432",
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

# Database

DATABASES = {"default": DATABASE_OPTIONS[get_database_key()]}

STATIC_URL = '/signals/static/'

STATIC_ROOT = '/static/'


HEALTH_MODEL = "signals.Signal"

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

DATAPUNT_AUTHZ = {"JWKS": os.getenv("PUB_JWKS", JWKS_TEST_KEY)}

SWAGGER_SETTINGS = {
   'USE_SESSION_AUTH': False,
   'SECURITY_DEFINITIONS': {
      'Signals API - Swagger': {
         'type': 'oauth2',
         'authorizationUrl': DATAPUNT_API_URL + "oauth2/authorize",
         'flow': 'implicit',
         'scopes': {
          'SIG/ALL': 'Signals all authorizations',
         }
      }
   },
   'OAUTH2_CONFIG': {
      'clientId': 'swagger-ui',
      # 'clientSecret': 'yourAppClientSecret',
      'appName': 'Signal Swagger UI'
   },
}
