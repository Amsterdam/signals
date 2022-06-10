# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
import logging

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
