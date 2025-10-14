# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2025 Delta10 B.V.

from typing import Optional

from signals import settings
from signals.apps.email_integrations.utils import _cleanup_signal_text
from signals.apps.signals.models import Signal


def make_text_context(signal: Signal, additional_context: Optional[dict] = None, dry_run: bool = False) -> dict:
    """
    Makes a context dictionary containing all values needed for the text templates
    Can add additional context, but will make sure that none of the default values are overridden.
    """
    # Decode the text and text_area before removing any URL to make sure that urlencoded URLs are also removed.
    text = _cleanup_signal_text(signal.text, dry_run=dry_run)
    text_extra = _cleanup_signal_text(signal.text_extra, dry_run=dry_run)

    assert signal.category_assignment is not None
    category = signal.category_assignment.category
    if category.parent and category.parent.public_name:
        # Category has a parent with a public name
        parent_public_name = category.parent.public_name
    elif category.parent and not category.parent.public_name:
        #  Category has a parent without a public name
        parent_public_name = category.parent.name
    else:
        # Fallback to a blank parent category name, this should not happen
        parent_public_name = ''

    assert signal.status is not None
    context = {
        'signal_id': signal.id,
        'formatted_signal_id': signal.get_id_display(),
        'created_at': signal.created_at,
        'text': text,
        'text_extra': text_extra,
        'address': signal.location.address if signal.location and signal.location.address else None,
        'status_text': signal.status.text,
        'status_state': signal.status.state,
        'handling_message': signal.category_assignment.stored_handling_message,
        'ORGANIZATION_NAME': settings.ORGANIZATION_NAME,
        'main_category_public_name': parent_public_name,
        'sub_category_public_name': category.public_name if category.public_name else category.name,
        'source': signal.source,
        'incident_date_start': signal.incident_date_start,
    }

    if additional_context:
        # Make sure the additional_context do not override the default context values
        for key in set(context).intersection(set(additional_context)):
            additional_context.pop(key)
        # Add the additional context
        context.update(additional_context)

    return context