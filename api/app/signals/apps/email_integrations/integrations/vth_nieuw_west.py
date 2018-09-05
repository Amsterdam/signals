"""
E-mail integration for VTH Nieuw West.
"""
from django.conf import settings
from django.core.mail import send_mail as django_send_mail

from signals.apps.email_integrations.utils import create_default_notification_message
from signals.apps.signals.models import Signal, STADSDEEL_NIEUWWEST


def send_mail(signal: Signal) -> int:
    """Send e-mail to VTH Nieuw West when applicable.

    :param signal: Signal object
    :returns: number of successfully send messages
    """
    if is_signal_applicable(signal):
        message = create_default_notification_message(signal)

        return django_send_mail(
            subject='Nieuwe melding op meldingen.amsterdam.nl',
            message=message,
            from_email=settings.NOREPLY,
            recipient_list=(settings.EMAIL_VTH_NIEUW_WEST_INTEGRATION_ADDRESS, ))

    return 0


def is_signal_applicable(signal: Signal) -> bool:
    """Is given `Signal` applicable for VTH Nieuw West.

    TODO SIG-409 refactor categories.

    :param signal: Signal object
    :returns: bool
    """
    if signal.location.stadsdeel != STADSDEEL_NIEUWWEST:
        return False

    eligible_main_category = 'Overlast Bedrijven en Horeca'
    eligible_sub_categories = (
        'Geluidsoverlast muziek',
        'Geluidsoverlast installaties',
        'Overlast terrassen',
        'Stankoverlast',
        'Overlast door bezoekers (niet op terras)',
    )
    is_applicable = (
        signal.category.main == eligible_main_category and
        signal.category.sub in eligible_sub_categories)

    return is_applicable

