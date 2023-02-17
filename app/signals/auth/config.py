# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
import types

from django.conf import settings as django_settings

from .errors import AuthConfigurationError

# A sentinel object for required settings
_required = object()

# The Django settings key
_settings_key = 'SIGNALS_AUTH'

# A list of all available settings, with default values
_available_settings = {
    'JWKS': "",
    'JWKS_URL': "",
    'ALLOWED_SIGNING_ALGORITHMS': [
        'HS256', 'HS384', 'HS512',
        'ES256', 'ES384', 'ES512',
        'RS256', 'RS384', 'RS512'
    ],
    'USER_ID_FIELDS': ''.split(','),  # fieldnames separated by comma's
    'ALWAYS_OK': False,
    'MIN_INTERVAL_KEYSET_UPDATE': 30
}

_settings = {}

# Preprocessing: the set of all available configuration keys
_available_settings_keys = set(_available_settings.keys())

# Preprocessing: the set of all required configuration keys
_required_settings_keys = {
    key for key, setting in _available_settings.items() if setting is _required
}


def init_settings():
    global _settings
    _settings = load_settings()


def get_settings():
    global _settings
    if not _settings:
        init_settings()
    return _settings


def load_settings():
    """ Fetch the settings.
    :return dict: settings
    """
    # Get the user-provided settings
    user_settings = dict(getattr(django_settings, _settings_key, {}))
    user_settings_keys = set(user_settings.keys())

    # Check for required but missing settings
    missing = _required_settings_keys - user_settings_keys
    if missing:
        raise AuthConfigurationError(
            'Missing required {} config: {}'.format(_settings_key, missing))

    # Check for unknown settings
    unknown = user_settings_keys - _available_settings_keys
    if unknown:
        raise AuthConfigurationError(
            'Unknown {} config params: {}'.format(_settings_key, unknown))

    # Merge defaults with provided settings
    defaults = _available_settings_keys - user_settings_keys
    user_settings.update({key: _available_settings[key] for key in defaults})

    if not user_settings.get('JWKS') and not user_settings.get('JWKS_URL'):
        raise AuthConfigurationError(
            'Either JWKS or JWKS_URL must be set, or both'
        )

    return types.MappingProxyType(user_settings)
