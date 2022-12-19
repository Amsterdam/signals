# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.conf import settings

# General settings
PAGE_SIZE = getattr(settings, 'GISIB_PAGE_SIZE', 15000)

# GISIB API settings
GISIB_ENDPOINT = getattr(settings, 'GISIB_ENDPOINT', None)
GISIB_USERNAME = getattr(settings, 'GISIB_USERNAME', None)
GISIB_PASSWORD = getattr(settings, 'GISIB_PASSWORD', None)
GISIB_APIKEY = getattr(settings, 'GISIB_APIKEY', None)
GISIB_LIMIT = getattr(settings, 'GISIB_LIMIT', 500)
