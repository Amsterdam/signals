# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2021 Gemeente Amsterdam
# Temporary fix to make the settings restructure work with current deployment settings. Can be
# removed after the Ansible playbooks for deployment are updated with the production settings.
import sys
from .base import *  # noqa
from .feature_flags import *
from logs import get_configuration

try:
    from .local import *
except ImportError:
    pass

if "test" in sys.argv or "pytest" in sys.argv[0]:
    try:
        from .testing import *
    except ImportError:
        pass

LOGGING = get_configuration(local_apps=SIGNAL_APPS, logging_level=LOGGING_LEVEL)

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': DATABASE_NAME,
        'USER': DATABASE_USER,
        'PASSWORD': DATABASE_PASSWORD,
        'HOST': DATABASE_HOST,
        'PORT': DATABASE_PORT
    },
}
