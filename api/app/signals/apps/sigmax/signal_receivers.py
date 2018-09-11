from django.dispatch import receiver

from signals.apps.sigmax import tasks
from signals.apps.signals.models import create_initial


@receiver(create_initial, dispatch_uid='signals_create_initial')
def create_initial_handler(sender, signal_obj, **kwargs):
    tasks.push_to_sigmax.delay(pk=signal_obj.id)
