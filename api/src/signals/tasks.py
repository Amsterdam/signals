import json
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template import loader
from django.utils import timezone

from signals.celery import app
from signals.models import Signal
from signals.utils.datawarehouse import save_csv_files_datawarehouse

log = logging.getLogger(__name__)


@app.task
def push_to_sigmax(id):
    pass


@app.task
def send_mail_apptimize(id):
    """Send email to Apptimize when applicable.

    :param id: Signal object id
    :returns:
    """
    try:
        signal = Signal.objects.get(id=id)
    except Signal.DoesNotExist as e:
        log.exception(str(e))
        return

    if _is_signal_applicable_for_apptimize(signal):
        message = json.dumps({
            'mora_nummer': signal.id,
            'signal_id': signal.signal_id,
            'tijdstip': signal.incident_date_start,
            'email_melder': signal.reporter.email,
            'telefoonnummer_melder': signal.reporter.phone,
            'adres': signal.location.address,
            'stadsdeel': signal.location.stadsdeel,
            'categorie': {
                'hoofdrubriek': signal.category.main,
                'subrubriek': signal.category.sub,
            },
            'omschrijving': signal.text,
        }, indent=4, sort_keys=True, default=str)

        send_mail(
            subject='Nieuwe melding op meldingen.amsterdam.nl',
            message=message,
            from_email=settings.NOREPLY,
            recipient_list=(settings.EMAIL_APPTIMIZE_INTEGRATION_ADDRESS, ),
            fail_silently=False)


def _is_signal_applicable_for_apptimize(signal):
    """Is given `Signal` applicable for Apptimize.

    Note, this logic isn't tenable anymore.. The concept `categories` needs
    to be refactored soon. Take a look at `signals.messaging.categories` as
    well.

    :param signal: Signal object
    :returns: bool
    """
    eligible_main_categories = ('Openbaar groen en water',
                                'Wegen, verkeer, straatmeubilair',
                                'Afval', )
    all_sub_categories_of_main_categories = (
        settings.SUB_CATEGORIES_DICT['Openbaar groen en water'] +
        settings.SUB_CATEGORIES_DICT['Wegen, verkeer, straatmeubilair'])

    eligible_sub_categories = ()
    for sub_category in all_sub_categories_of_main_categories:
        eligible_sub_categories += (sub_category[2], )
    eligible_sub_categories += ('Prullenbak is vol', 'Veeg- / zwerfvuil', )

    is_applicable_for_apptimize = (
        settings.EMAIL_APPTIMIZE_INTEGRATION_ADDRESS is not None
        and signal.category.main in eligible_main_categories
        and signal.category.sub in eligible_sub_categories)

    return is_applicable_for_apptimize


@app.task
def send_mail_flex_horeca(id):
    """Send email to Flex Horeca Team when applicable.

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
