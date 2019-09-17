from django.dispatch import receiver

from signals.apps.email_integrations.flex_horeca import tasks
from signals.apps.signals.managers import create_child, create_initial, update_category_assignment


@receiver(create_initial, dispatch_uid='flex_horeca_email_create_initial')
def create_initial_handler(sender, signal_obj, **kwargs):
    tasks.send_mail_flex_horeca.delay(pk=signal_obj.id)


@receiver(create_child, dispatch_uid='flex_horeca_email_create_child')
def create_child_handler(sender, signal_obj, **kwargs):
    tasks.send_mail_flex_horeca.delay(pk=signal_obj.id)


@receiver(update_category_assignment, dispatch_uid='flex_horeca_email_update_category_assignment')
def update_category_assignment_handler(sender, signal_obj, **kwargs):
    tasks.send_mail_flex_horeca.delay(pk=signal_obj.id)
