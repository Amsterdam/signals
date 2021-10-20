# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
from django import http


class AuthConfigurationError(Exception):
    """ Error for missing / invalid configuration"""


class AuthorizationHeaderError(Exception):
    def __init__(self, response):
        self.response = response


def invalid_request():
    msg = (
        "Bearer realm=\"Signals\", error=\"invalid_request\", "
        "error_description=\"Invalid Authorization header format; "
        "should be: 'Bearer [token]'\"")
    response = http.HttpResponse('Bad Request', status=400)
    response['WWW-Authenticate'] = msg
    return response
