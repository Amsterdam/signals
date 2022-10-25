# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
import logging

from django.utils import timezone
from elasticsearch import NotFoundError

from signals.apps.search.documents.signal import SignalDocument
from signals.apps.signals.models import Signal
from signals.celery import app

log = logging.getLogger(__name__)


@app.task
def save_to_elastic(signal_id):
    if not SignalDocument.ping():
        raise Exception('Elastic cluster is unreachable')

    signal = Signal.objects.get(id=signal_id)
    signal_document = SignalDocument.create_document(signal)
    signal_document.save()


@app.task
def rebuild_index():
    log.info('rebuild_index - start')

    if not SignalDocument.ping():
        raise Exception('Elastic cluster is unreachable')

    SignalDocument.index_documents()
    log.info('rebuild_index - done!')


@app.task
def delete_from_elastic(signal):
    if not SignalDocument.ping():
        raise Exception('Elastic cluster is unreachable')

    if isinstance(signal, int):
        signal = Signal.objects.get(id=signal)

    signal_document = SignalDocument.create_document(signal)

    try:
        signal_document.delete()
    except NotFoundError:
        log.warning(f'Signal {signal.id} not found in Elasticsearch')


@app.task
def index_signals_updated_in_date_range(from_date, to_date):
    """
    Index all Signals updated in the given date range (Copied from the elastic_index management command)
    """
    if not SignalDocument.ping():
        raise Exception('Elastic cluster is unreachable')

    if from_date:
        from_date = timezone.make_aware(timezone.datetime.strptime(from_date, '%Y-%m-%d'))
    else:
        # Default is 2 days ago
        from_date = timezone.now() - timezone.timedelta(days=2)

    from_date = from_date.replace(hour=00, minute=00, second=00)  # Beginning of the day given in from_date

    if to_date:
        to_date = timezone.make_aware(timezone.datetime.strptime(to_date, '%Y-%m-%d'))
    else:
        # Default is today
        to_date = timezone.now()

    to_date = to_date + timezone.timedelta(days=1)
    to_date = to_date.replace(hour=00, minute=00, second=00)  # Beginning of the day after the to_date

    log.info(f'index_signals_updated_in_date_range - from {from_date}, to {to_date}')

    if to_date < from_date:
        log.warning('To date cannot be before the from date')
        return

    signal_qs = Signal.objects.filter(updated_at__range=[from_date, to_date]).order_by('-updated_at')
    SignalDocument.index_documents(queryset=signal_qs)

    log.info('index_signals_updated_in_date_range - done!')
