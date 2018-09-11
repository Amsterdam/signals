import logging
from typing import Optional

from signals.apps.sigmax import handler as sigmax
from signals.apps.signals.models import Signal
from signals.celery import app

logger = logging.getLogger(__name__)


def retrieve_signal(pk: int) -> Optional[Signal]:
    try:
        signal = Signal.objects.get(id=pk)
    except Signal.DoesNotExist as e:
        logger.exception(str(e))
        return None
    return signal


@app.task
def push_to_sigmax(pk: int):
    """
    Send signals to Sigmax if applicable

    :param pk:
    :return: Nothing
    """
    signal: Signal = retrieve_signal(pk)
    if signal and sigmax.is_signal_applicable(signal):
        sigmax.handle(signal)
