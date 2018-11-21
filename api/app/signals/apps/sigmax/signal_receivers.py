from django.dispatch import receiver

from signals.apps.sigmax import tasks
from signals.apps.signals.managers import update_status


@receiver(update_status, dispatch_uid='sigmax_update_status')
def update_status_handler(sender, signal_obj, status, prev_status, **kwargs):
    # call via Celery signal sending code
    tasks.push_to_sigmax.delay(pk=signal_obj.id)
