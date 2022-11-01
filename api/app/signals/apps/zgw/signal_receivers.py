# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2022 Delta10 B.V.
from django.dispatch import receiver

from signals.apps.signals.managers import create_initial, update_status
from . import tasks

@receiver(create_initial, dispatch_uid='zgw_create_initial')
def create_initial_handler(sender, signal_obj, *args, **kwargs):
    tasks.create_initial.delay(signal_id=signal_obj.pk)

@receiver(update_status, dispatch_uid='zgw_update_status')
def update_status_handler(sender, signal_obj, status, *args, **kwargs):
    tasks.update_status.delay(status_id=status.pk)
