# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2022 Gemeente Amsterdam
import os

from .base import INSTALLED_APPS
from .feature_flags import FEATURE_FLAGS

LOGGING_LEVEL = "INFO"

ALLOWED_HOSTS = ['*']

CORS_ALLOWED_ORIGINS = [
    'http://127.0.0.1',
    'https://127.0.0.1',
    'http://0.0.0.0',
    'https://0.0.0.0',
]
CORS_ALLOW_ALL_ORIGINS = False

DATABASE_HOST = os.getenv('DATABASE_HOST', 'database')
DATABASE_PORT = '5432'

SECRET_KEY = 'insecure'
CELERY_TASK_ALWAYS_EAGER = True
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
TEST_LOGIN = 'signals.admin@example.com'
SITE_DOMAIN = 'localhost:8000'

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

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

SIGNALS_AUTH = {
    'JWKS': JWKS_TEST_KEY,  # noqa
    'ALWAYS_OK': True,
    'USER_ID_FIELDS': 'email'.split(',')
}

FRONTEND_URL = 'http://dummy_link'

INSTALLED_APPS += [  # noqa
    'change_log.tests',  # Added so that we can test the chane_log with a "test only" model
]

FEATURE_FLAGS['SYSTEM_MAIL_FEEDBACK_RECEIVED_ENABLED'] = True
FEATURE_FLAGS['REPORTER_MAIL_HANDLED_NEGATIVE_CONTACT_ENABLED'] = True
FEATURE_FLAGS['SIGNAL_HISTORY_LOG_ENABLED'] = True
