# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2023 Gemeente Amsterdam
# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from signals.celery import app as celery_app
from signals.utils.version import get_version

__all__ = ['celery_app', 'VERSION', 'API_VERSIONS', ]

# Versioning
# ==========
# SIA / Signalen follows the semantic versioning standard. For backwards
# compatibility, and to not break external systems that rely on
# SIA / Signalen we still expose all the separate version numbers, but
# they are now all the same.

# Application version (Major, minor, patch)
VERSION = (2, 22, 1)

API_VERSIONS = {
    'v1': VERSION,
}

__version__ = get_version(VERSION)
