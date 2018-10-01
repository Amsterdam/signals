import logging
from typing import Optional

# from signals.apps.sigmax import outgoing as sigmax
from signals.apps.sigmax import outgoing
from signals.apps.signals.models import Signal
from signals.apps.signals import workflow
from signals.celery import app

logger = logging.getLogger(__name__)


def retrieve_signal(pk: int) -> Optional[Signal]:
    try:
        signal = Signal.objects.get(id=pk)
    except Signal.DoesNotExist as e:
        logger.exception(str(e))
        return None
    return signal


def is_signal_applicable(signal):
    """Check that signal instance should be sent to Sigmax/CityControl."""
    # TODO: use choice constant on Status model
    if (signal.status.state == workflow.TE_VERZENDEN and
        signal.status.external_api == 'sigmax'):
        return True
    return False


@app.task
def push_to_sigmax(pk: int):
    """
    Send signals to Sigmax if applicable

    :param pk:
    :return: Nothing
    """
    signal: Signal = retrieve_signal(pk)
    if is_signal_applicable(signal):
        pass
