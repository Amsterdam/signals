# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.contrib import admin

from signals.apps.signals.models import CategoryDepartment


class CategoryDepartmentInline(admin.TabularInline):
    raw_id_fields = ('category', 'department',)
    model = CategoryDepartment
    extra = 0


class DepartmentAdmin(admin.ModelAdmin):
    inlines = (CategoryDepartmentInline, )
    fields = ('code', 'name', 'is_intern', 'can_direct')
    list_display = ('code', 'name', 'is_intern', 'can_direct')
    ordering = ('name',)
    list_per_page = 20
