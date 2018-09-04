from django.dispatch import receiver

from signals.apps.email_integrations.tasks import send_mail_apptimize, send_mail_flex_horeca
from signals.apps.signals.signal_declarations import create_initial


@receiver(create_initial, dispatch_uid='email_integrations_create_initial')
def create_initial_handler(sender, signal_obj, **kwargs):
    send_mail_apptimize.delay(pk=signal_obj.id)
    send_mail_flex_horeca.delay(pk=signal_obj.id)
