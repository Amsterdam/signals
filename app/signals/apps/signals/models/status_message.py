# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from typing import List

from django.db import models

from signals.apps.signals import workflow
from signals.apps.signals.models import Category, CreatedUpdatedModel


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
    categories : List[Category]
        The categories that this status message is attached to.
    """
    title: str = models.CharField(max_length=255)
    text: str = models.TextField()
    active: bool = models.BooleanField(default=False)
    state: str = models.CharField(max_length=50, choices=workflow.STATUS_CHOICES)
    categories: List[Category] = models.ManyToManyField(Category, through='StatusMessageCategory')


class StatusMessageCategory(models.Model):
    """
    Intermediary model to be able to define the position of a status message within a
    category.

    Attributes
    ----------
    status_message : StatusMessage
        The status message.
    category : Category
        The category to which the status message is attached.
    position : int
        The position of the status message within the list of status messages that are
        attached to a category. This field should be used to order the status messages
        for a specific category. That way they can be displayed in the configured order.
    """
    status_message: StatusMessage = models.ForeignKey(StatusMessage, on_delete=models.CASCADE)
    category: Category = models.ForeignKey(Category, on_delete=models.CASCADE)
    position: int = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['status_message', 'category'],
                name='%(app_label)s_%(class)s_unique_constraint'
            )
        ]
