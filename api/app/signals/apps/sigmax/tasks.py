import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from signals.apps.sigmax.stuf_protocol.outgoing import handle
from signals.apps.signals import workflow
from signals.apps.signals.models import Signal, Status
from signals.celery import app

logger = logging.getLogger(__name__)


def is_signal_applicable(signal):
    """Check that signal instance should be sent to Sigmax/CityControl."""
    return signal.status.state == workflow.TE_VERZENDEN and \
        signal.status.target_api == Status.TARGET_API_SIGMAX


@app.task
def push_to_sigmax(pk):
    """
    Send signals to Sigmax if applicable

    :param pk:
    :return: Nothing
    """
    try:
        signal = Signal.objects.get(pk=pk)
    except Signal.DoesNotExist:
        logger.exception()
        return None

    if is_signal_applicable(signal):
        handle(signal)


@app.task
def fail_stuck_sending_signals():
    before = timezone.now() - timedelta(minutes=settings.SIGMAX_SEND_FAIL_TIMEOUT_MINUTES)
    stuck_signals = Signal.objects.filter(status__state=workflow.TE_VERZENDEN,
                                          status__target_api=Status.TARGET_API_SIGMAX,
                                          status__updated_at__lte=before)

    for signal in stuck_signals:
        Signal.actions.update_status(data={
            'state': workflow.VERZENDEN_MISLUKT,
            'text': 'Melding stond langer dan {} minuten op TE_VERZENDEN. Mislukt'.format(
                settings.SIGMAX_SEND_FAIL_TIMEOUT_MINUTES
            )
        }, signal=signal)
