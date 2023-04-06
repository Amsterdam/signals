# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    """
    Convert a Django ValidationError to a DRF ValidationError.
    """
    if isinstance(exc, DjangoValidationError):
        if hasattr(exc, 'message') and exc.message:
            exc = DRFValidationError(exc.message)
        elif hasattr(exc, 'message_dict') and exc.message_dict:
            exc = DRFValidationError(exc.message_dict)
        else:
            exc = DRFValidationError('Validation error on underlying data.')

    response = exception_handler(exc, context)

    return response
