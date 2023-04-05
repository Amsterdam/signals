# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # Produce json response with validation errors
    if response is None and isinstance(exc, ValidationError):
        response = JsonResponse(
            {'errors': exc.message_dict},
            status=status.HTTP_400_BAD_REQUEST
        )

    return response
