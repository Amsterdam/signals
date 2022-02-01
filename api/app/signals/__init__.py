# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2021 Gemeente Amsterdam
# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from signals.celery import app as celery_app
from signals.utils.version import get_version

__all__ = ['celery_app', 'VERSION', 'API_VERSIONS', ]

# Workaround an import issue in Django REST Framework Extensions, see:
# https://github.com/chibisov/drf-extensions/issues/294
# These lines can be removed when a new version is released (> 0.6.0)
from django.db.models.sql import datastructures  # noqa
from django.core.exceptions import EmptyResultSet  # noqa

datastructures.EmptyResultSet = EmptyResultSet
# ---


# Versioning
# ==========
# SIA / Signalen follows the semantic versioning standard. Previously we had
# separate version numbers for the V0 (now defunct) and V1 versions of the API.
# We now no longer separately version these, as their releases were always
# tied to the backend. For backwards compatibility, and to not break external
# systems that rely on SIA / Signalen we still expose all the separate version
# numbers, but they are now all the same.


# Application version (Major, minor, patch)
VERSION = (2, 3, 5)

API_VERSIONS = {
    'v0': VERSION,
    'v1': VERSION,
}

__version__ = get_version(VERSION)
