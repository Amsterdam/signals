"""
E-mail integration for VTH Nieuw West.
"""
from django.conf import settings
from django.core.mail import send_mail as django_send_mail
from django.db.models import Q
from django.utils import timezone

from signals.apps.email_integrations.utils import (
    create_default_notification_message,
    is_business_hour
)
from signals.apps.signals.models import STADSDEEL_NIEUWWEST, Category, Signal


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
    # We're only sending notification e-mails when the current Dutch time is outside
    # business / working hours.
    current_dutch_time = timezone.localtime(timezone.now()).time()
    if is_business_hour(current_dutch_time):
        return False

    if signal.location.stadsdeel != STADSDEEL_NIEUWWEST:
        return False

    # TODO: move this query to object manager.
    eligible_categories = Category.objects.filter(
        Q(main_category__slug='overlast-bedrijven-en-horeca') & (
            Q(slug='geluidsoverlast-muziek') |
            Q(slug='geluidsoverlast-installaties') |
            Q(slug='overlast-terrassen') |
            Q(slug='stankoverlast') |
            Q(slug='overlast-door-bezoekers-niet-op-terras')))

    return signal.category_assignment.category in eligible_categories
