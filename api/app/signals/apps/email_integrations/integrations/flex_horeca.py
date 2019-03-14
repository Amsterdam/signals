"""
E-mail integration for Flex Horeca Team.
"""
from datetime import datetime

from django.conf import settings
from django.core.mail import send_mail as django_send_mail
from django.utils import timezone

from signals.apps.email_integrations.utils import create_default_notification_message
from signals.apps.signals.models import Category, Signal


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

    Flex Horeca Team can't check the Signals Dashboard on friday and saterday (night). That's why we
    send them an e-mail notification on these days for new `Signal` objects that are created.

    :param signal: Signal object
    :returns: bool
    """
    applicable_weekdays_setting = settings.EMAIL_FLEX_HORECA_WEEKDAYS.split(',')
    applicable_weekdays = [int(weekday) for weekday in applicable_weekdays_setting]
    today = timezone.localtime(timezone.now())  # Current datetime in the Netherlands
    today_weekday = today.isoweekday()

    # Is 'today' an applicable weekday.
    is_today_applicable = today_weekday in applicable_weekdays
    if not is_today_applicable:
        return False

    # Is 'today' last applicable weekday, check end time.
    is_today_last_applicable_weekday = today_weekday == applicable_weekdays[-1]
    end_time = datetime.strptime(settings.EMAIL_FLEX_HORECA_END_TIME, '%H:%M').time()
    is_now_gt_end_time = today.time() > end_time
    if is_today_last_applicable_weekday and is_now_gt_end_time:
        return False

    # TODO: move this query to object manager.
    eligible_categories = Category.objects.filter(
        main_category__slug='overlast-bedrijven-en-horeca')

    return signal.category_assignment.category in eligible_categories
