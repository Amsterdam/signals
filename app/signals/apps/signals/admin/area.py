# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 - 2023 Gemeente Amsterdam
from django.contrib.gis.admin import GISModelAdmin


class AreaAdmin(GISModelAdmin):
    search_fields = ['name', 'code', '_type__name', '_type__code']
    list_display = ['name', 'code', '_type']
    list_filter = ['_type__code']
