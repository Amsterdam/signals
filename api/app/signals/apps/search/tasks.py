import logging

from django.conf import settings

from signals.apps.search.documents.signal import SignalDocument
from signals.apps.signals.models import Signal
from signals.celery import app

log = logging.getLogger(__name__)


@app.task
def save_to_elastic(signal_id):
    if not settings.FEATURE_FLAGS.get('SEARCH_BUILD_INDEX', False):
        log.warning('rebuild_index - elastic indexing disabled')
    else:
        signal = Signal.objects.get(id=signal_id)
        signal_document = SignalDocument.create_document(signal)
        signal_document.save()


@app.task
def rebuild_index():
    if not settings.FEATURE_FLAGS.get('SEARCH_BUILD_INDEX', False):
        log.warning('rebuild_index - elastic indexing disabled')
    else:
        log.info('rebuild_index - start')
        SignalDocument.index_documents()
        log.info('rebuild_index - done!')
