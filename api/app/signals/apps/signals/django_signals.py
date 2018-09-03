from django.dispatch import receiver

from signals.apps.signals import tasks
from signals.apps.signals.models import (
    Status, create_initial, update_location,
    update_status, update_category, update_reporter)
from signals.messaging.send_emails import handle_create_signal, handle_status_change


@receiver(create_initial, dispatch_uid='create_initial')
def create_initial_handler(sender, signal_obj, **kwargs):
    handle_create_signal(signal_obj)
    tasks.push_to_sigmax.delay(pk=signal_obj.id)
    tasks.send_mail_flex_horeca.delay(pk=signal_obj.id)
    tasks.send_mail_apptimize.delay(pk=signal_obj.id)


@receiver(update_location, dispatch_uid='update_location')
def update_location_handler(sender, location, **kwargs):
    tasks.send_mail_apptimize.delay(pk=location.signal.id)


@receiver(update_status, dispatch_uid='update_status')
def update_status_handler(sender, status, **kwargs):
    previous_status = Status.objects.exclude(id=status.id).last()
    handle_status_change(status, previous_status)
    tasks.send_mail_apptimize.delay(pk=status.signal.id)


@receiver(update_category, dispatch_uid='update_category')
def update_category_handler(sender, category, **kwargs):
    tasks.send_mail_apptimize.delay(pk=category.signal.id)


@receiver(update_reporter, dispatch_uid='update_reporter')
def update_reporter_handler(sender, reporter, **kwargs):
    tasks.send_mail_apptimize.delay(pk=reporter.signal.id)
