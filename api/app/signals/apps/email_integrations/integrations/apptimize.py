import json

from django.conf import settings
from django.core.mail import send_mail as django_send_mail

from signals.apps.signals.models import Signal


def send_mail(signal: Signal) -> int:
    """Send e-mail to Apptimize when applicable.

    :param signal: Signal object
    :returns: number of successfully send messages
    """
    if is_signal_applicable(signal):
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

        return django_send_mail(
            subject='Nieuwe melding op meldingen.amsterdam.nl',
            message=message,
            from_email=settings.NOREPLY,
            recipient_list=(settings.EMAIL_APPTIMIZE_INTEGRATION_ADDRESS, ))

    return 0


def is_signal_applicable(signal: Signal) -> bool:
    """Is given `Signal` applicable for Apptimize.

    TODO SIG-409 refactor categories.
    Note, this logic isn't tenable anymore.. The concept `categories` needs
    to be refactored soon. Take a look at `signals.messaging.categories` as
    well.

    :param signal: Signal object
    :returns: bool
    """
    eligible_main_categories = ('Openbaar groen en water',
                                'Wegen, verkeer, straatmeubilair',
                                'Afval',)
    all_sub_categories_of_main_categories = (
            settings.SUB_CATEGORIES_DICT['Openbaar groen en water'] +
            settings.SUB_CATEGORIES_DICT['Wegen, verkeer, straatmeubilair'])

    eligible_sub_categories = ()
    for sub_category in all_sub_categories_of_main_categories:
        eligible_sub_categories += (sub_category[2],)
    eligible_sub_categories += ('Prullenbak is vol', 'Veeg- / zwerfvuil',)

    is_applicable_for_apptimize = (
            settings.EMAIL_APPTIMIZE_INTEGRATION_ADDRESS is not None
            and signal.category.main in eligible_main_categories
            and signal.category.sub in eligible_sub_categories)

    return is_applicable_for_apptimize
