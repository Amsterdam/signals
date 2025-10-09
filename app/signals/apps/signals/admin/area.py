# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 - 2023 Gemeente Amsterdam
from django.contrib.gis.admin import GISModelAdmin
from import_export.admin import ExportActionMixin, ImportExportModelAdmin

from signals.apps.signals.resources import AreaResource, AreaTypeResource


class AreaAdmin(ImportExportModelAdmin, ExportActionMixin, GISModelAdmin):
    resource_class = AreaResource

    search_fields = ['name', 'code', '_type__name', '_type__code']
    list_display = ['name', 'code', '_type']
    list_filter = ['_type__code']


class AreaTypeAdmin(ImportExportModelAdmin, ExportActionMixin):
    resource_class = AreaTypeResource

    search_fields = ['name', 'code']
    list_display = ['name', 'code', 'description']
