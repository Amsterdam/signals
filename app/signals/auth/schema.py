# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.plumbing import build_bearer_security_scheme_object


class AccessTokenAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = 'signals.auth.backend.JWTAuthBackend'
    name = 'JWTAuthBackend'

    def get_security_definition(self, auto_schema):
        return build_bearer_security_scheme_object(header_name='AUTHORIZATION',
                                                   token_prefix='Bearer',
                                                   bearer_format='JWT')
