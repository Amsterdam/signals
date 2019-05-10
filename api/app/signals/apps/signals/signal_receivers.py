from django.dispatch import receiver

from signals.apps.signals import tasks
from signals.apps.signals.managers import create_child, create_initial


@receiver(create_initial, dispatch_uid='signals_create_initial')
def create_initial_handler(sender, signals_obj, **kwargs):
    tasks.translate_category(signals_obj)


@receiver(create_child, disparch_uid='signals_create_child')
def create_child_handler(sender, signals_obj, **kwargs):
    tasks.translate_category(signals_obj)
