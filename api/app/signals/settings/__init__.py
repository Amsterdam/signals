# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2021 Gemeente Amsterdam
# Temporary fix to make the settings restructure work with current deployment settings. Can be
# removed after the Ansible playbooks for deployment are updated with the production settings.
import os, sys # noqa

from logs import get_configuration

from .base import *  # noqa
from .feature_flags import * # noqa

if "test" in sys.argv or "pytest" in sys.argv[0] or os.getenv('TESTING') == 'true':
    try:
        from .testing import * # noqa
    except ImportError:
        pass

else:
    try:
        from .local import *  # noqa
    except ImportError:
        pass

LOGGING = get_configuration(local_apps=SIGNAL_APPS, logging_level=LOGGING_LEVEL) # noqa

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': DATABASE_NAME, # noqa:
        'USER': DATABASE_USER, # noqa
        'PASSWORD': DATABASE_PASSWORD, # noqa
        'HOST': DATABASE_HOST, # noqa
        'PORT': DATABASE_PORT # noqa
    },
} # noqa
