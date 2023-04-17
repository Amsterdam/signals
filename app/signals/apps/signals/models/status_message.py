# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from django.db import models

from signals.apps.signals.models import CreatedUpdatedModel


class StatusMessage(CreatedUpdatedModel):
    """
    This model supersedes the StatusMessageTemplate model.
    It allows for storing default texts that can be used to inform the reporter on a
    status change of a signal.

    Attributes
    ----------
    title : str
        The title of the status message.
    text : str
        The actual text of the status message.
    active : bool
        The "active" state of the status message. This determines if it should be used
        to inform reporters.
    """
    title: str = models.CharField(max_length=255)
    text: str = models.TextField()
    active: bool = models.BooleanField(default=False)
