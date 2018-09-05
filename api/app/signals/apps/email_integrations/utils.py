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
