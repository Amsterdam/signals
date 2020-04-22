from jwcrypto.common import JWException
from jwcrypto.jwk import JWKSet

from .config import AuthzConfigurationError, get_settings

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
    settings = get_settings()
    load_jwks(settings['JWKS'])

    if len(_keyset['keys']) == 0:
        raise AuthzConfigurationError('No keys loaded!')


def load_jwks(jwks):
    global _keyset
    try:
        _keyset.import_keyset(jwks)
    except JWException:
        raise AuthzConfigurationError("Failed to import keyset from settings")
