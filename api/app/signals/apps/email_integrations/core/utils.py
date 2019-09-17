from datetime import time

from django.template import loader

from signals.apps.signals.models import Signal


def create_default_notification_message(signal: Signal) -> str:
    """Create (default) notification message for e-mail body.

    :param signal: Signal object
    :returns: message body
    """
    template = loader.get_template('email/default_notification_message.txt')
    context = {'signal': signal, }
    message = template.render(context)

    return message


def is_business_hour(given_time: time) -> bool:
    """Is the given time a business hour.

    Business / working hours is: "working from 9:00 to 17:00"

    :returns: bool
    """
    business_start_time = time(9, 0)  # 09:00:00
    business_end_time = time(17, 0)  # 17:00:00
    return business_start_time <= given_time <= business_end_time
