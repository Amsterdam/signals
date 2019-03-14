"""
E-mail integration for Apptimize.
"""
import json

from django.conf import settings
from django.core.mail import send_mail as django_send_mail
from django.db.models import Q

from signals.apps.signals.models import Category, Signal


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
                'hoofdrubriek': signal.category_assignment.category.parent.name,
                'subrubriek': signal.category_assignment.category.name,
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

    :param signal: Signal object
    :returns: bool
    """
    # TODO: move this query to object manager.
    eligible_categories = Category.objects.filter(
        Q(parent__slug='openbaar-groen-en-water') |
        Q(parent__slug='wegen-verkeer-straatmeubilair') |
        Q(parent__slug='afval', slug='prullenbak-is-vol') |
        Q(parent__slug='afval', slug='prullenbak-is-kapot') |
        Q(parent__slug='afval', slug='veeg-zwerfvuil'))

    is_applicable_for_apptimize = (
            settings.EMAIL_APPTIMIZE_INTEGRATION_ADDRESS is not None
            and signal.category_assignment.category in eligible_categories)

    return is_applicable_for_apptimize
