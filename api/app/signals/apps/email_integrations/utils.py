from datetime import time
from django.utils import timezone
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


def is_now_business_hour() -> bool:
    """Is the current time in the Netherlands a business hour.

    Business / working hours is: "working from 9:00 to 17:00"

    :returns: bool
    """
    now_time = timezone.localtime(timezone.now()).time()  # Current time in the Netherlands
    business_start_time = time(9, 0)  # 09:00:00
    business_end_time = time(17, 0)  # 17:00:00
    return business_start_time <= now_time <= business_end_time
