# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from signals.apps.search.documents.status_message import StatusMessage as StatusMessageDocument
from signals.apps.signals.models import StatusMessage as StatusMessageModel


def transform(instance: StatusMessageModel) -> StatusMessageDocument:
    """Transforms a status message database model into a status message elasticsearch document.

    Parameters
    ----------
    instance : StatusMessageModel
        The instance of the database model to be transformed.

    Returns
    -------
    StatusMessageDocument
        An elasticsearch document based on the database model.
    """
    document = StatusMessageDocument()
    document.meta['id'] = instance.id
    document.id = instance.id
    document.title = instance.title
    document.text = instance.text
    document.active = instance.active
    document.state = instance.state

    return document
