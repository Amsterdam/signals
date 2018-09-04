from django.dispatch import receiver

from signals.apps.email_integrations import tasks
from signals.apps.signals.models import (
    create_initial,
    update_location,
    update_status,
    update_category,
    update_reporter
)


@receiver(create_initial, dispatch_uid='email_integrations_create_initial')
def create_initial_handler(sender, signal_obj, **kwargs):
    tasks.send_mail_reporter(signal=signal_obj)
    tasks.send_mail_apptimize.delay(pk=signal_obj.id)
    tasks.send_mail_flex_horeca.delay(pk=signal_obj.id)


@receiver(update_location, dispatch_uid='email_integrations_update_location')
def update_location_handler(sender, signal_obj, location, prev_location, **kwargs):
    tasks.send_mail_apptimize.delay(pk=signal_obj.id)


@receiver(update_status, dispatch_uid='email_integrations_update_status')
def update_status_handler(sender, signal_obj, status, prev_status, **kwargs):
    tasks.send_mail_status_change(status, prev_status)
    tasks.send_mail_apptimize.delay(pk=signal_obj.id)


@receiver(update_category, dispatch_uid='email_integrations_update_category')
def update_category_handler(sender, signal_obj, category, prev_category, **kwargs):
    tasks.send_mail_apptimize.delay(pk=signal_obj.id)


@receiver(update_reporter, dispatch_uid='email_integrations_update_reporter')
def update_reporter_handler(sender, signal_obj, reporter, prev_reporter, **kwargs):
    tasks.send_mail_apptimize.delay(pk=signal_obj.id)
