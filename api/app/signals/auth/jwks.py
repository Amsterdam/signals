import time

import requests
from jwcrypto.common import JWException
from jwcrypto.jwk import JWKSet

from .config import AuthzConfigurationError, get_settings

_keyset = None
_keyset_last_update = 0


def get_keyset():
    global _keyset
    if not _keyset:
        init_keyset()
    return _keyset


def check_update_keyset():
    """
    When loading a JWKS from a url (public endpoint), we might need to
    check sometimes if the JWKS has changed. To avoid too many requests to
    the url, we set a minimal interval between two checks.
    """
    settings = get_settings()
    current_time = time.time()
    if current_time - _keyset_last_update >= settings['MIN_INTERVAL_KEYSET_UPDATE']:
        init_keyset()


def init_keyset():
    """
    Initialize keyset, by loading keyset from settings
    """
    global _keyset

    _keyset = JWKSet()
    settings = get_settings()

    if settings.get('JWKS'):
        load_jwks(settings['JWKS'])

    if settings.get('JWKS_URL'):
        load_jwks_from_url(settings['JWKS_URL'])

    if len(_keyset['keys']) == 0:
        raise AuthzConfigurationError('No keys loaded!')


def load_jwks(jwks):
    global _keyset
    try:
        _keyset.import_keyset(jwks)
    except JWException:
        raise AuthzConfigurationError("Failed to import keyset from settings")


def load_jwks_from_url(jwks_url):
    global _keyset
    try:
        response = requests.get(jwks_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise AuthzConfigurationError(
            "Failed to get Keycloak keyset from url: {}, error: {}".format(jwks_url, e)
        )
    try:
        _keyset.import_keyset(response.text)
    except JWException as e:
        raise AuthzConfigurationError("Failed to import Keycloak keyset") from e
