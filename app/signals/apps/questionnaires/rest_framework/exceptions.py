# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from rest_framework.exceptions import APIException
from rest_framework.status import HTTP_410_GONE


class Gone(APIException):
    status_code = HTTP_410_GONE
    default_detail = 'Gone'
    default_code = 'gone'
