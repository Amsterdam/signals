from django.conf import settings
from django.core.mail import send_mail as django_send_mail

from signals.apps.email_integrations.core.utils import create_default_notification_message
from signals.apps.email_integrations.settings import app_settings
from signals.apps.signals.models import Signal


def send_mail(signal: Signal) -> int:
    """Send e-mail to Toezicht openbare ruimte Nieuw west when applicable.

    :param signal: Signal object
    :returns: number of successfully send messages
    """
    subject = 'Nieuwe melding op meldingen.amsterdam.nl'
    message = create_default_notification_message(signal)
    from_email = settings.NOREPLY
    recipient_list = app_settings.TOEZICHT_OR_NIEUW_WEST['RECIPIENT_LIST']

    return django_send_mail(subject=subject, message=message, from_email=from_email,
                            recipient_list=recipient_list)
