# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
import time

from django.conf import settings
from jwcrypto.jwk import JWKSet

_keyset = None

def get_keyset():
    global _keyset
    if not _keyset:
        init_keyset()
    return _keyset

def init_keyset():
    """
    Initialize keyset, by loading keyset from settings
    """
    global _keyset

    _keyset = JWKSet()

    if settings.PUB_JWKS:
        _keyset.import_keyset(settings.PUB_JWKS)

    if len(_keyset['keys']) == 0:
        raise Exception('No keys loaded!')
