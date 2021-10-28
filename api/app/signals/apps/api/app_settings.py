# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from django.conf import settings

from signals.apps.signals import workflow

SIGNALS_API_MAX_UPLOAD_SIZE = 8388608  # 8MB = 8*1024*1024
SIGNALS_API_ATLAS_SEARCH_URL = settings.DATAPUNT_API_URL + 'atlas/search'
SIGNALS_API_PDOK_API_URL = 'https://geodata.nationaalgeoregister.nl'

SIGNALS_API_CLOSED_STATES = frozenset([
    workflow.AFGEHANDELD,
    workflow.GEANNULEERD,
    workflow.GESPLITST,
])
SIGNALS_API_STATE_CLOSED = 'CLOSED'
SIGNALS_API_STATE_CLOSED_DISPLAY = 'Gesloten'
SIGNAL_API_STATE_OPEN = 'OPEN'
SIGNAL_API_STATE_OPEN_DISPLAY = 'Open'

SIGNAL_CONTEXT_GEOGRAPHY_RADIUS = 50  # Radius in meters
SIGNAL_CONTEXT_GEOGRAPHY_CREATED_DELTA_WEEKS = 12  # Created gte X weeks ago
