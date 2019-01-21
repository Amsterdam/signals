"""
E-mail integration for Apptimize.
"""
import json

from django.conf import settings
from django.core.mail import send_mail as django_send_mail
from django.db.models import Q

from signals.apps.signals.models import Signal, SubCategory


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
                'hoofdrubriek': signal.category_assignment.sub_category.main_category.name,
                'subrubriek': signal.category_assignment.sub_category.name,
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
    eligible_sub_categories = SubCategory.objects.filter(
        Q(main_category__slug='openbaar-groen-en-water') |
        Q(main_category__slug='wegen-verkeer-straatmeubilair') |
        Q(main_category__slug='afval', slug='prullenbak-is-vol') |
        Q(main_category__slug='afval', slug='prullenbak-is-kapot') |
        Q(main_category__slug='afval', slug='veeg-zwerfvuil'))

    is_applicable_for_apptimize = (
            settings.EMAIL_APPTIMIZE_INTEGRATION_ADDRESS is not None
            and signal.category_assignment.sub_category in eligible_sub_categories)

    return is_applicable_for_apptimize
