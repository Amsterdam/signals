# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from django.db import models

from signals.apps.signals import workflow
from signals.apps.signals.models import CreatedUpdatedModel


class StatusMessage(CreatedUpdatedModel):
    """
    This model supersedes the StatusMessageTemplate model.
    It allows for storing default texts that can be used to inform the reporter on a
    status change of a signal.
    A status message belongs to a signal state and can be assigned to multiple
    categories.

    Attributes
    ----------
    title : str
        The title of the status message.
    text : str
        The actual text of the status message.
    active : bool
        The "active" state of the status message. This determines if it should be used
        to inform reporters.
    state : str
        When transitioning a signal to this state, this status message should be
        available to inform the reporter.
    """
    title: str = models.CharField(max_length=255)
    text: str = models.TextField()
    active: bool = models.BooleanField(default=False)
    state: str = models.CharField(max_length=50, choices=workflow.STATUS_CHOICES)
