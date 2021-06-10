# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import APIException
from rest_framework.status import (
    HTTP_412_PRECONDITION_FAILED,
    HTTP_501_NOT_IMPLEMENTED,
    HTTP_504_GATEWAY_TIMEOUT
)


class PreconditionFailed(APIException):
    status_code = HTTP_412_PRECONDITION_FAILED
    default_detail = _('Precondition failed.')
    default_code = 'precondition_failed'


class NotImplementedException(APIException):
    status_code = HTTP_501_NOT_IMPLEMENTED
    default_detail = 'Not implemented'


class GatewayTimeoutException(APIException):
    status_code = HTTP_504_GATEWAY_TIMEOUT
    default_detail = 'A server error occurred.'
