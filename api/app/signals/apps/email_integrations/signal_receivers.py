from django.dispatch import receiver

from signals.apps.email_integrations import tasks
from signals.apps.signals.managers import create_initial, update_status


@receiver(create_initial, dispatch_uid='reporter_email_integrations_create_initial')
def create_initial_handler(sender, signal_obj, *args, **kwargs):
    tasks.send_mail_reporter.delay(pk=signal_obj.pk)


@receiver(update_status, dispatch_uid='core_email_integrations_update_status')
def update_status_handler(sender, signal_obj, status, prev_status, *args, **kwargs):
    tasks.send_mail_reporter.delay(pk=signal_obj.pk)
