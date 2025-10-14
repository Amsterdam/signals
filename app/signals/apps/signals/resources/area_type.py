# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2025 Delta10 B.V.

from import_export import resources

from signals.apps.signals.models import AreaType


class AreaTypeResource(resources.ModelResource):
    class Meta:
        model = AreaType
        import_id_fields = ('code',)
        exclude = ('id',)
