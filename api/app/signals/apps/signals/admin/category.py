# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.contrib import admin
from django.db.models import Q

from signals.apps.history.services import HistoryLogService
from signals.apps.signals.models import Category, ServiceLevelObjective


class ParentCategoryFilter(admin.SimpleListFilter):
    title = 'Parent category'
    parameter_name = 'parent__id'

    def lookups(self, request, model_admin):
        return [
            (category.pk, category.__str__())
            for category in Category.objects.filter(parent__isnull=True).iterator()
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(Q(parent__id=self.value()) | Q(id=self.value()))
        return queryset.all()


class CategoryTypeFilter(admin.SimpleListFilter):
    title = 'Category type'
    parameter_name = 'type'

    def lookups(self, request, model_admin):
        return [
            (category.pk, category.__str__())
            for category in Category.objects.filter(parent__isnull=True).iterator()
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(Q(parent__id=self.value()) | Q(id=self.value()))
        return queryset.all()


class CategoryDepartmentInline(admin.TabularInline):
    raw_id_fields = ('department',)
    model = Category.departments.through
    extra = 1


class ServiceLevelObjectiveInline(admin.TabularInline):
    model = ServiceLevelObjective
    fields = ('n_days', 'use_calendar_days', 'created_at',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    radio_fields = {'use_calendar_days': admin.HORIZONTAL}
    extra = 1

    def has_delete_permission(self, request, obj=None):
        return False


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'public_name', 'parent', 'is_active', 'is_public_accessible',)
    list_per_page = 20
    list_filter = ('is_active', 'is_public_accessible', ParentCategoryFilter,)
    sortable_by = ('name', 'parent', 'is_active',)

    inlines = (ServiceLevelObjectiveInline, CategoryDepartmentInline,)
    fields = ('name', 'slug', 'parent', 'is_active', 'description', 'handling_message', 'public_name',
              'is_public_accessible', 'icon',)
    readonly_fields = ('slug',)
    view_on_site = True

    search_fields = ('name', 'public_name',)
    ordering = ('parent__name', 'name',)

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        """
        On the save from the model also add an history log in the admin panel
        """

        obj.save()
        if change:  # only trigger when an object has been changed
            HistoryLogService.log_update(instance=obj, user=request.user)


class ChildCategoryFilter(admin.SimpleListFilter):
    title = 'Child category'
    parameter_name = 'category_id'

    def lookups(self, request, model_admin):
        return [
            (category.pk, category.__str__())
            for category in Category.objects.iterator()
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(category__id=self.value())
        return queryset.all()


class StatusMessageTemplatesAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'state', 'order', 'text',)
    list_display_links = list_display
    list_filter = (ChildCategoryFilter,)
