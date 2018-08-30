from django.db.models.signals import post_save
from django.dispatch import receiver

from signals.apps.signals import tasks
from signals.apps.signals.models import (
    Signal, create_initial, update_location,
    update_status, update_category, update_reporter)


@receiver(create_initial, dispatch_uid='create_initial')
def create_initial_handler(sender, signal, **kwargs):
    pass


@receiver(update_location, dispatch_uid='update_location')
def update_location_handler(sender, location, **kwargs):
    pass


@receiver(update_status, dispatch_uid='update_status')
def update_status_handler(sender, status, **kwargs):
    pass


@receiver(update_category, dispatch_uid='update_category')
def update_category_handler(sender, category, **kwargs):
    pass


@receiver(update_reporter, dispatch_uid='update_reporter')
def update_reporter_handler(sender, reporter, **kwargs):
    pass


@receiver(post_save, sender=Signal, dispatch_uid='post_save_signal')
def post_save_signal(sender, instance, created, **kwargs):
    if created:
        tasks.push_to_sigmax.delay(pk=instance.id)
        tasks.send_mail_flex_horeca.delay(pk=instance.id)
    tasks.send_mail_apptimize.delay(pk=instance.id)
