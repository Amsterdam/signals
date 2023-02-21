# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2023 Gemeente Amsterdam
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import APIException
from rest_framework.status import HTTP_504_GATEWAY_TIMEOUT


class GatewayTimeoutException(APIException):
    status_code = HTTP_504_GATEWAY_TIMEOUT
    default_detail = _('A server error occurred.')
