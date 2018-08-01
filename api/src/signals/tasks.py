import json
import logging

from django.conf import settings
from django.core.mail import send_mail

from signals.celery import app
from signals.models import Signal

log = logging.getLogger(__name__)


@app.task
def push_to_sigmax(id):
    pass


@app.task
def email_apptimize(id):
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
            subject='email',
            message=message,
            from_email=settings.NOREPLY,
            recipient_list=(settings.EMAIL_APPTIMIZE_INTEGRATION_ADDRESS, ),
            fail_silently=False
        )


def _is_signal_applicable_for_apptimize(signal):
    """Is given `Signal` applicable for Apptimize.

    :param signal: Signal object
    :returns: bool
    """
    eligible_main_categories = ('Openbaar groen en water',
                                'Wegen/verkeer/straatmeubilair', )
    eligible_sub_categories = ()
    for main_category in eligible_main_categories:
        for sub_category in settings.SUB_CATEGORIES_DICT[main_category]:
            eligible_sub_categories += (sub_category[2], )

    is_eligible_for_apptimize = (
        settings.EMAIL_APPTIMIZE_INTEGRATION_ADDRESS
        and signal.category.main in eligible_main_categories
        and signal.category.sub in eligible_sub_categories)

    return is_eligible_for_apptimize
