# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 -2024 Gemeente Amsterdam
import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from signals.apps.search.documents.status_message import StatusMessage as StatusMessageDocument
from signals.apps.search.tasks import delete_from_elastic, save_to_elastic
from signals.apps.search.transformers.status_message import transform
from signals.apps.signals.managers import (
    create_child,
    create_initial,
    update_category_assignment,
    update_location,
    update_priority,
    update_type
)
from signals.apps.signals.models import Signal
from signals.apps.signals.models import StatusMessage as StatusMessageModel
from signals.apps.signals.models.reporter import Reporter, reporter_anonymized


@receiver(
    [
        create_initial,
        create_child,
        update_location,
        update_category_assignment,
        update_priority,
        update_type,
    ],
    dispatch_uid='search_add_to_elastic'
)
def add_to_elastic_handler(sender, signal_obj, **kwargs):
    # Add to elastic
    save_to_elastic.delay(signal_id=signal_obj.id)


@receiver(post_save, sender=StatusMessageModel, dispatch_uid='status_message_post_save_receiver')
def status_message_post_save_receiver(sender: str, instance: StatusMessageModel, **kwargs):
    """Django signal receiver used to index StatusMessage models in elasticsearch
    after they're saved in the database.

    Parameters
    ----------
    sender : str
        The classname of the model. This should always be the classname of the
        StatusMessage model, which is defined in the @receiver decorator above.
    instance : StatusMessageModel
        The instance of the StatusMessage model that was saved to the database.
    """
    document = transform(instance)
    document.save(refresh='true')


@receiver(post_delete, sender=StatusMessageModel, dispatch_uid='status_message_post_delete_receiver')
def status_message_post_delete_receiver(sender: str, instance: StatusMessageModel, **kwargs):
    """Django signal receiver used to delete status message documents from the
    elasticsearch index after they have been deleted from the database.

    Parameters
    ----------
    sender : str
        The classname of the model. This should always be the classname of the
        StatusMessage model, which is defined in the @receiver decorator above.
    instance : StatusMessageModel
        The instance of the StatusMessage model that was saved to the database.
    """
    document = StatusMessageDocument.get(instance.id)
    document.delete(refresh='true')


@receiver(post_delete, sender=Signal, dispatch_uid='signal_post_deleted_receiver')
def signal_post_deleted_receiver(sender: str, instance: Signal, **kwargs):
    """Django signal receiver used to delete Signal documents from the
    elasticsearch index after they have been deleted from the database.

    Parameters
    ----------
    sender : str
        The classname of the model. This should always be the classname of the
        Signal model, which is defined in the @receiver decorator above.
    instance : Signal
        The instance of the Signal model that was deleted from the database.
    """
    try:
        delete_from_elastic(signal=instance)
    except Exception as e:
        logging.error(f'Exception when deleting signal #{instance.id} from elastic: {e}')


@receiver(reporter_anonymized, sender=Reporter, dispatch_uid='reporter_anonymized_receiver')
def reporter_anonymized_receiver(sender: str, instance: Reporter, **kwargs) -> None:
    """Django signal receiver used to re-index a signal in elastic search when the reporter is anonymized."""
    save_to_elastic.delay(signal_id=instance.signal.id)
