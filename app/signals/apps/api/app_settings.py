# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2023 Gemeente Amsterdam
from signals.apps.signals import workflow

SIGNALS_API_CLOSED_STATES = frozenset([
    workflow.AFGEHANDELD,
    workflow.GEANNULEERD,
    workflow.GESPLITST,
])
SIGNALS_API_STATE_CLOSED = 'CLOSED'
SIGNALS_API_STATE_CLOSED_DISPLAY = 'Gesloten'
SIGNAL_API_STATE_OPEN = 'OPEN'
SIGNAL_API_STATE_OPEN_DISPLAY = 'Open'
