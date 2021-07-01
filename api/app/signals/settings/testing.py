# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2021 Gemeente Amsterdam
from signals.settings.base import *  # noqa

SECRET_KEY = 'insecure'
CELERY_TASK_ALWAYS_EAGER = True
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
TEST_LOGIN = 'signals.admin@example.com'
SITE_DOMAIN = 'localhost:8000'
INSTALLED_APPS += [  # noqa
    'change_log.tests',  # Added so that we can test the chane_log with a "test only" model
]

SIGNALS_AUTHZ = {
    'JWKS': JWKS_TEST_KEY,  # noqa
    'ALWAYS_OK': True,
    'USER_ID_FIELDS': 'sub,email'.split(',')
}

FEATURE_FLAGS['API_SEARCH_ENABLED'] = False  # noqa F405
FEATURE_FLAGS['SEARCH_BUILD_INDEX'] = False  # noqa F405

FRONTEND_URL = 'http://dummy_link'
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {'nouser': os.getenv('PUBLIC_THROTTLE_RATE', '60/m')} # noqa