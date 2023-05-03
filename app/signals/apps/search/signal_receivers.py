# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from signals.apps.search.tasks import (
    index_status_message,
    remove_status_message_from_index,
    save_to_elastic
)
from signals.apps.signals.managers import (
    create_child,
    create_initial,
    update_category_assignment,
    update_location,
    update_priority,
    update_type
)
from signals.apps.signals.models import StatusMessage as StatusMessageModel


@receiver([create_initial,
           create_child,
           update_location,
           update_category_assignment,
           update_priority,
           update_type], dispatch_uid='search_add_to_elastic')
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
    index_status_message.delay(status_message_id=instance.id)


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
    remove_status_message_from_index.delay(status_message_id=instance.id)
