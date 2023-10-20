# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 - 2023 Gemeente Amsterdam
import uuid
from typing import TYPE_CHECKING

from django.contrib.gis.db import models
from django.db.models import Model

from signals.apps.signals import workflow

if TYPE_CHECKING:
    from signals.apps.signals.models import Signal


class DeleteSignalManager(models.Manager):
    def create_from_signal(self, signal: "Signal", action: str, note: str, deleted_by: str | None = None,
                           batch_uuid: uuid.UUID | None = None):
        assert signal.status
        assert signal.category_assignment and signal.category_assignment.category

        return super().create(
            # Fields to store from the given Signal
            signal_id=signal.id,
            signal_uuid=signal.uuid,
            parent_signal_id=signal.parent_id,
            category=signal.category_assignment.category,
            signal_state=signal.status.state,
            signal_state_set_at=signal.status.created_at,
            signal_created_at=signal.created_at,

            # Administration fields
            deleted_by=deleted_by, action=action, note=note, batch_uuid=batch_uuid
        )


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

    # Administration fields

    # Who deleted the Signal, a null/blank value indicates the system user has deleted the Signal
    deleted_by = models.EmailField(null=True, blank=True, editable=False)

    # When a Signal was deleted
    deleted_at = models.DateTimeField(editable=False, auto_now_add=True)

    # If the Signals are deleted in bulk this can be set to recognize the run
    # Used when deleting Signals by running the "delete_signals" Django management command
    batch_uuid = models.UUIDField(null=True, blank=True, editable=False)

    # Indicates if an automatic or manual action deleted the Signal
    action = models.CharField(choices=(('automatic', 'Automatic'), ('manual', 'Manual'), ), max_length=12,
                              editable=False)

    # Note explaining why a Signal has been deleted
    note = models.TextField(null=True, blank=True, editable=False)

    # Custom manager that helps with creating an instance

    objects = DeleteSignalManager()
