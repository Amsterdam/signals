from django.utils import timezone
from django.utils.datetime_safe import datetime

from signals.apps.email_integrations.settings import app_settings
from signals.apps.signals.models import Category, Signal


def is_signal_applicable(signal: Signal) -> bool:
    """Is given `Signal` applicable for Flex Horeca Team.

    Flex Horeca Team can't check the Signals Dashboard on friday and saterday (night). That's why we
    send them an e-mail notification on these days for new `Signal` objects that are created.

    :param signal: Signal object
    :returns: bool
    """
    applicable_weekdays_setting = app_settings.FLEX_HORECA['APPLICABLE_RULES']['WEEKDAYS'].split(',')  # noqa
    applicable_weekdays = [int(weekday) for weekday in applicable_weekdays_setting]
    today = timezone.localtime(timezone.now())  # Current datetime in the Netherlands
    today_weekday = today.isoweekday()

    # Is 'today' an applicable weekday.
    is_today_applicable = today_weekday in applicable_weekdays
    if not is_today_applicable:
        return False

    # Is 'today' last applicable weekday, check end time.
    is_today_last_applicable_weekday = today_weekday == applicable_weekdays[-1]
    end_time = datetime.strptime(app_settings.FLEX_HORECA['APPLICABLE_RULES']['END_TIME'], '%H:%M').time()  # noqa
    is_now_gt_end_time = today.time() > end_time
    if is_today_last_applicable_weekday and is_now_gt_end_time:
        return False

    eligible_categories = Category.objects.filter(parent__slug='overlast-bedrijven-en-horeca')

    return signal.category_assignment.category in eligible_categories
