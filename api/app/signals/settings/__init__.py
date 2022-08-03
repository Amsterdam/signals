# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2022 Gemeente Amsterdam
from logs import get_configuration

from .base import *  # noqa

LOGGING = get_configuration(local_apps=SIGNAL_APPS, logging_level=LOGGING_LEVEL) # noqa
