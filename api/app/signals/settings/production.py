# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2021 Gemeente Amsterdam
import os

from signals.settings.base import *  # noqa

DATABASES['default']['HOST'] = os.getenv('DATABASE_HOST_OVERRIDE')  # noqa: F405
DATABASES['default']['PORT'] = os.getenv('DATABASE_PORT_OVERRIDE')  # noqa: F405

# Django security settings
SECURE_SSL_REDIRECT = True
SECURE_REDIRECT_EXEMPT = [r'^status/', ]  # Allow health checks on localhost.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SIGNALS_AUTH['USER_ID_FIELDS'] = os.getenv('USER_ID_FIELDS', 'email').split(',')  # noqa F405
