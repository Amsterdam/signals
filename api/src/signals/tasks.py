import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template import loader
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


@app.task
def send_mail_flex_horeca(id):
    """Send email to Flex Horeca Team when applicable

    :param id: Signal object id
    :returns:
    """
    try:
        signal = Signal.objects.get(id=id)
    except Signal.DoesNotExist as e:
        log.exception(str(e))
        return

    if _is_signal_applicable_for_flex_horeca(signal):
        template = loader.get_template('mail_flex_horeca.txt')
        context = {'signal': signal, }
        message = template.render(context)
        send_mail(
            subject='Nieuwe melding op meldingen.amsterdam.nl',
            message=message,
            from_email=settings.NOREPLY,
            recipient_list=(settings.EMAIL_FLEX_HORECA_INTEGRATION_ADDRESS, ),
            fail_silently=False)


def _is_signal_applicable_for_flex_horeca(signal):
    """Is given `Signal` applicable for Flex Horeca Team.

    :param signal: Signal object
    :returns: bool
    """
    pass
