import logging

from typing import Optional

from signals.celery import app
from signals.integrations.apptimize import handler as apptimize
from signals.integrations.sigmax import handler as sigmax
from signals.models import Signal

log = logging.getLogger(__name__)


def retrieve_signal(pk: int) -> Optional[Signal]:
    try:
        signal = Signal.objects.get(id=pk)
    except Signal.DoesNotExist as e:
        log.exception(str(e))
        return None
    return signal


@app.task
def push_to_sigmax(key: int):
    """
    Send signals to Sigmax if applicable
    :param key:
    :return: Nothing
    """
    signal: Signal = retrieve_signal(key)
    if signal and sigmax.is_signal_applicable(signal):
        sigmax.handle(signal)


@app.task
def send_mail_apptimize(key: int):
    """Send email to Apptimize when applicable.
    :param key: Signal object id
    :returns:
    """
    signal: Signal = retrieve_signal(key)
    if signal and apptimize.is_signal_applicable(signal):
        apptimize.handle(signal)
