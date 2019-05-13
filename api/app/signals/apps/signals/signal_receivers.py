from django.dispatch import receiver

from signals.apps.signals import tasks
from signals.apps.signals.managers import create_child, create_initial


@receiver(create_initial, dispatch_uid='signals_create_initial')
def signals_create_initial_handler(sender, signal_obj, **kwargs):
    tasks.translate_category(signal_obj.id)


@receiver(create_child, dispatch_uid='signals_create_child')
def signals_create_child_handler(sender, signal_obj, **kwargs):
    tasks.translate_category(signal_obj.id)
