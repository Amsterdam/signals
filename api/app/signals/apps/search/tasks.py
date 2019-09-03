import logging
from pathlib import Path

from django.utils import timezone

from signals.apps.search.documents.signal import SignalDocument
from signals.apps.signals.models import Signal
from signals.celery import app

log = logging.getLogger(__name__)


@app.task
def save_to_elastic(signal_id):
    signal = Signal.objects.get(id=signal_id)
    signal_document = SignalDocument.create_document(signal)
    signal_document.save()


@app.task
def rebuild_index():
    log.info('rebuild_index - start')

    lock_file = Path('/tmp/rebuild_index.lock')
    if lock_file.exists():
        log.warning('rebuild_index - task is either still running or failed!')
        return

    log.info('rebuild_index - creating lock file')
    lock_file.write_text(str(timezone.now()))

    log.debug('rebuild_index - clear the index')
    SignalDocument.clear_index()

    log.debug('rebuild_index - rebuild the index')
    SignalDocument.index_documents()

    log.info('rebuild_index - removing lock file')
    lock_file.unlink()

    log.info('rebuild_index - done!')
