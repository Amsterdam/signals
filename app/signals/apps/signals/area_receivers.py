# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2026 Delta10 B.V.

from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from import_export.signals import post_import

from signals.apps.signals.area_cache import invalidate_area_cache
from signals.apps.signals.models import Area, AreaType


@receiver(post_save, sender=Area, dispatch_uid='invalidate_area_cache_area_save')
@receiver(post_delete, sender=Area, dispatch_uid='invalidate_area_cache_area_delete')
@receiver(post_save, sender=AreaType, dispatch_uid='invalidate_area_cache_area_type_save')
@receiver(post_delete, sender=AreaType, dispatch_uid='invalidate_area_cache_area_type_delete')
def invalidate_signal_context_area_cache(sender, **kwargs) -> None:
    transaction.on_commit(invalidate_area_cache)


@receiver(post_import, dispatch_uid='invalidate_area_cache_after_area_import')
def invalidate_signal_context_area_cache_after_import(sender, model, **kwargs) -> None:
    # django-import-export sends post_import with sender=None and model=<imported model>.
    if model not in (Area, AreaType):
        return

    transaction.on_commit(invalidate_area_cache)
