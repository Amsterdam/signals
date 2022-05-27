# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.contrib.gis.db import models
from django.db.models import Model

from signals.apps.signals import workflow


class DeleteSignalManager(models.Manager):
    def create_from_signal(self, signal, deleted_by=None, batch_uuid=None):
        return super().create(signal_id=signal.id,
                              signal_uuid=signal.uuid,
                              parent_signal_id=signal.parent_id,
                              category=signal.category_assignment.category,
                              signal_state=signal.status.state,
                              signal_state_set_at=signal.status.created_at,
                              signal_created_at=signal.created_at,
                              deleted_by=deleted_by,
                              batch_uuid=batch_uuid)


class DeletedSignal(Model):
    """
    Model for storing meta data of deleted Signals
    """

    # The ID of the signal that was deleted
    signal_id = models.PositiveBigIntegerField(editable=False)

    # The UUID of the signal that was deleted
    signal_uuid = models.UUIDField(editable=False)

    # The parent of the signal that was deleted
    parent_signal_id = models.PositiveBigIntegerField(null=True, blank=True, editable=False)

    # The category the Signal was in
    category = models.ForeignKey('signals.Category', on_delete=models.DO_NOTHING, related_name='+', editable=False)

    # The state of the signal when it was deleted
    signal_state = models.CharField(max_length=20, blank=True, choices=workflow.STATUS_CHOICES, editable=False)

    # The date the state was set
    signal_state_set_at = models.DateTimeField(editable=False)

    # The date the Signal was created
    signal_created_at = models.DateTimeField(editable=False)

    # Who deleted the Signal, a null/blank value indicates the system user has deleted the Signal
    deleted_by = models.EmailField(null=True, blank=True, editable=False)

    # When a Signal was deleted
    deleted_at = models.DateTimeField(editable=False, auto_now_add=True)

    # If the Signals are deleted in bulk this can be set to recognize the run
    # Used when deleting Signals by running the "delete_signals" Django management command
    batch_uuid = models.UUIDField(null=True, blank=True, editable=False)

    objects = DeleteSignalManager()


class DeletedSignalLog(Model):
    """
    Model for logging all actions when deleting a Signal
    """

    deleted_signal = models.ForeignKey('signals.DeletedSignal', on_delete=models.DO_NOTHING, related_name='log')

    # Indicates if an automatic or manual action deleted the Signal
    action = models.CharField(choices=(('automatic', 'Automatic'), ('manual', 'Manual'), ), max_length=12,
                              editable=False)

    # Note explaining why a Signal has been deleted
    note = models.TextField(null=True, blank=True, editable=False)

    # Who deleted the Signal, a null/blank value indicates the system user has deleted the Signal
    created_by = models.EmailField(null=True, blank=True, editable=False)

    # When a Signal was deleted
    created_at = models.DateTimeField(editable=False, auto_now_add=True)
