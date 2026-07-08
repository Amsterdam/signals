# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2026 Delta10 B.V.

from uuid import uuid4

from django.core.cache import cache

AREA_CACHE_VERSION_KEY = 'signal_context_areas_version'
AREA_CACHE_DEFAULT_VERSION = 'initial'


def get_area_cache_version() -> str:
    return cache.get(AREA_CACHE_VERSION_KEY, AREA_CACHE_DEFAULT_VERSION)


def invalidate_area_cache() -> None:
    cache.set(AREA_CACHE_VERSION_KEY, uuid4().hex, timeout=None)
