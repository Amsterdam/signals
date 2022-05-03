# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.contrib import admin


class SourceAdmin(admin.ModelAdmin):
    fields = ('name', 'description', 'is_active', 'is_public', 'can_be_selected', 'order', )
