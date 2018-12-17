import logging

# from signals.apps.sigmax import outgoing as sigmax
from signals.apps.sigmax import outgoing
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
        try:
            success_message = outgoing.handle(signal)
        except outgoing.SigmaxException:
            Signal.actions.update_status({
                'state': workflow.VERZENDEN_MISLUKT,
                'text': 'Verzending van melding naar THOR is mislukt.',
            }, signal=signal)
            raise  # Fail task in Celery.
        else:
            Signal.actions.update_status({
                'state': workflow.VERZONDEN,
                'text': success_message,
            }, signal=signal)
