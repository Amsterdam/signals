import logging

from django.conf import settings

from signals.apps.search.documents.signal import SignalDocument
from signals.apps.signals.models import Signal
from signals.celery import app

log = logging.getLogger(__name__)


@app.task
def save_to_elastic(signal_id):
    if settings.FEATURE_FLAGS.get('SEARCH_BUILD_INDEX', False):
        signal = Signal.objects.get(id=signal_id)
        signal_document = SignalDocument.create_document(signal)
        signal_document.save()
    else:
        log.warning('rebuild_index - elastic indexing disabled')


@app.task
def rebuild_index():
    if settings.FEATURE_FLAGS.get('SEARCH_BUILD_INDEX', False):
        log.info('rebuild_index - start')
        SignalDocument.index_documents()
        log.info('rebuild_index - done!')
    else:
        log.warning('rebuild_index - elastic indexing disabled')
