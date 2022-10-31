# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2021 Delta10 B.V.
from django.contrib import admin
from .models import Case


@admin.register(Case)
class EmailTemplate(admin.ModelAdmin):
    list_display = [
        '_signal',
        'external_id'
    ]

    readonly_fields = [
        '_signal',
        'external_id'
    ]

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
