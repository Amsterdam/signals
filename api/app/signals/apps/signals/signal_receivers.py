# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from django.dispatch import receiver

from signals.apps.signals import tasks
from signals.apps.signals.managers import create_initial, update_status


@receiver(create_initial, dispatch_uid='signals_create_initial')
def signals_create_initial_handler(sender, signal_obj, **kwargs):
    tasks.apply_routing(signal_obj.id)
    tasks.apply_auto_create_children.apply_async(kwargs={'signal_id': signal_obj.id}, countdown=30)


@receiver(update_status, dispatch_uid='signals_update_status')
def update_status_handler(sender, signal_obj, status, prev_status, *args, **kwargs):
    tasks.update_status_children_based_on_parent(signal_id=signal_obj.pk)
