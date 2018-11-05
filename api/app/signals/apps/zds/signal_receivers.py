from django.dispatch import receiver

from signals.apps.signals.models import create_initial, update_status
from signals.apps.zds import tasks


@receiver(create_initial, dispatch_uid='zds_create_case')
def create_case_handler(sender, signal_obj, **kwargs):
    """
    Simply creating a case is not enough. We also need to connect the signal
    to the case.

    So the following tasks should be called.
    - create_case
    - connect_signal_to_case
    - add_status_to_case
    - add_photo_to_case if there is a photo.
    """
    signal = tasks.create_case(signal_obj)
    tasks.connect_signal_to_case(signal)
    tasks.add_status_to_case(signal)

    if signal.image:
        tasks.create_document(image)
        tasks.add_photo_to_case(signal)


@receiver(update_status, dispatch_uid='zds_update_status')
def update_status_handler(sender, signal_obj, status, prev_status, **kwargs):
    tasks.add_status_to_case(signal_obj)
