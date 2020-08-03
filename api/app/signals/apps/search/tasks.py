import logging

from signals.apps.search.documents.signal import SignalDocument
from signals.apps.signals.models import Signal
from signals.celery import app

log = logging.getLogger(__name__)


@app.task
def save_to_elastic(signal_id):
    if not SignalDocument.ping():
        raise Exception('Elastic cluster is down')

    signal = Signal.objects.get(id=signal_id)
    signal_document = SignalDocument.create_document(signal)
    signal_document.save()


@app.task
def rebuild_index():
    log.info('rebuild_index - start')

    if not SignalDocument.ping():
        raise Exception('Elastic cluster is down')

    SignalDocument.index_documents()
    log.info('rebuild_index - done!')
