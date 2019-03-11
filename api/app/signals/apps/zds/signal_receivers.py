from django.core.exceptions import ObjectDoesNotExist
from django.dispatch import receiver

from signals.apps.signals.managers import add_image, create_initial, update_status
from signals.apps.zds import tasks
from signals.apps.zds.exceptions import (
    CaseConnectionException,
    CaseNotCreatedException,
    DocumentConnectionException,
    DocumentNotCreatedException,
    StatusNotCreatedException
)

# TODO: when the ZDS integration is updated, it should also listen to
# `create_child` DjangoSignals (these are used when new SIA Signals are
# created after a split action).


@receiver(create_initial, dispatch_uid='zds_create_case')
def create_initial_handler(sender, signal_obj, **kwargs):
    """
    Simply creating a case is not enough. We also need to connect the signal
    to the case.

    So the following tasks should be called.
    - create_case
    - connect_signal_to_case
    - add_status_to_case
    - add_document_to_case if there is a photo.
    """
    try:
        tasks.create_case(signal_obj)
        tasks.connect_signal_to_case(signal_obj)
        tasks.add_status_to_case(signal_obj, signal_obj.status)

        if signal_obj.image:
            try:
                case_document = tasks.create_document(signal_obj)
                tasks.add_document_to_case(signal_obj, case_document)
            except (DocumentNotCreatedException, DocumentConnectionException):
                pass

    except (CaseNotCreatedException, CaseConnectionException, StatusNotCreatedException):
        pass


@receiver(update_status, dispatch_uid='zds_update_status')
def update_status_handler(sender, signal_obj, status, prev_status, **kwargs):
    try:
        tasks.add_status_to_case(signal_obj, status)
    except ObjectDoesNotExist:
        pass


@receiver(add_image, dispatch_uid='zds_add_image')
def add_image_handler(sender, signal_obj, **kwargs):
    try:
        case_document = tasks.create_document(signal_obj)
        tasks.add_document_to_case(signal_obj, case_document)
    except (DocumentNotCreatedException, ObjectDoesNotExist):
        pass
