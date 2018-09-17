"""
E-mail integration for Flex Horeca Team.
"""
from django.conf import settings
from django.core.mail import send_mail as django_send_mail
from django.utils import timezone

from signals.apps.email_integrations.utils import create_default_notification_message
from signals.apps.signals.models import Signal


def send_mail(signal: Signal) -> int:
    """Send e-mail to Flex Horeca Team when applicable.

    :param signal: Signal object
    :returns: number of successfully send messages
    """
    if is_signal_applicable(signal):
        message = create_default_notification_message(signal)

        return django_send_mail(
            subject='Nieuwe melding op meldingen.amsterdam.nl',
            message=message,
            from_email=settings.NOREPLY,
            recipient_list=(settings.EMAIL_FLEX_HORECA_INTEGRATION_ADDRESS, ))

    return 0


def is_signal_applicable(signal: Signal) -> bool:
    """Is given `Signal` applicable for Flex Horeca Team.

    Flex Horeca Team can't check the Signals Dashboard on friday and saterday. That's why we send
    them an e-mail notification on these days for new `Signal` objects that are created.

    TODO SIG-409 refactor categories.

    :param signal: Signal object
    :returns: bool
    """
    # Default: `'5,6'` (friday, saterday).
    applicable_weekdays_setting = settings.EMAIL_FLEX_HORECA_WEEKDAYS.split(',')
    applicable_weekdays = [int(weekday) for weekday in applicable_weekdays_setting]

    today = timezone.localtime(timezone.now())  # Current datetime in the Netherlands
    weekday = today.isoweekday()
    is_weekday_applicable = weekday in applicable_weekdays
    if not is_weekday_applicable:
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
