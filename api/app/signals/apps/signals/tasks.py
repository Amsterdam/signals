import logging
from typing import Optional

from django.conf import settings
from django.core.mail import send_mail
from django.template import loader
from django.utils import timezone

from signals.apps.signals.models import Signal
from signals.celery import app
from signals.integrations.apptimize import handler as apptimize
from signals.integrations.sigmax import handler as sigmax
from signals.utils.datawarehouse import save_csv_files_datawarehouse

log = logging.getLogger(__name__)


def retrieve_signal(pk: int) -> Optional[Signal]:
    try:
        signal = Signal.objects.get(id=pk)
    except Signal.DoesNotExist as e:
        log.exception(str(e))
        return None
    return signal


@app.task
def push_to_sigmax(pk: int):
    """
    Send signals to Sigmax if applicable
    :param key:
    :return: Nothing
    """
    signal: Signal = retrieve_signal(pk)
    if signal and sigmax.is_signal_applicable(signal):
        sigmax.handle(signal)


@app.task
def send_mail_apptimize(pk: int):
    """Send email to Apptimize when applicable.
    :param key: Signal object id
    :returns:
    """
    signal: Signal = retrieve_signal(pk)
    if signal and apptimize.is_signal_applicable(signal):
        apptimize.handle(signal)


@app.task
def send_mail_flex_horeca(pk):
    """Send email to Flex Horeca Team when applicable.

    :param pk: Signal object id
    :returns:
    """
    try:
        signal = Signal.objects.get(id=pk)
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
            recipient_list=(settings.EMAIL_FLEX_HORECA_INTEGRATION_ADDRESS,),
            fail_silently=False)


def _is_signal_applicable_for_flex_horeca(signal):
    """Is given `Signal` applicable for Flex Horeca Team.

    Flex Horeca Team can't check the Signals Dashboard on friday and
    saterday. That's why we send them an e-mail notification on these days
    for new `Signal` objects that are created.

    :param signal: Signal object
    :returns: bool
    """
    today = timezone.now()
    weekday = today.isoweekday()
    is_friday_or_saterday = weekday == 5 or weekday == 6
    if not is_friday_or_saterday:
        return False

    eligible_main_categories = 'Overlast Bedrijven en Horeca'
    eligible_sub_categories = (
        'Geluidsoverlast muziek',
        'Geluidsoverlast installaties',
        'Overlast terrassen',
        'Stankoverlast')
    is_applicable_for_flex_horeca = (
            signal.category.main == eligible_main_categories
            and signal.category.sub in eligible_sub_categories)

    return is_applicable_for_flex_horeca


@app.task
def task_save_csv_files_datawarehouse():
    """Celery task to save CSV files for Datawarehouse.

    This task is scheduled in Celery beat to run periodically.

    :returns:
    """
    save_csv_files_datawarehouse()
