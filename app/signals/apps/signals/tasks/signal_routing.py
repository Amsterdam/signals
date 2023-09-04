# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
import logging

from django.db.utils import OperationalError

from signals.apps.services.domain.dsl import SignalDslService
from signals.apps.signals.models.signal import Signal
from signals.celery import app

log = logging.getLogger(__name__)


# OperationalError catches the psycopg2.errors.LockNotAvailable exception
@app.task(autoretry_for=(OperationalError, ), max_retries=5, default_retry_delay=10)
def apply_routing(signal_id):
    signal = Signal.objects.get(pk=signal_id)
    SignalDslService().process_routing_rules(signal)
