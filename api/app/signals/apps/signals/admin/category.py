# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
import csv

from django.contrib import admin
from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone

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
              'is_public_accessible',)
    readonly_fields = ('slug',)
    view_on_site = True

    search_fields = ('name', 'public_name',)
    ordering = ('parent__name', 'name',)

    actions = ['download_csv']

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        """
        On the save from the model also add an history log in the admin panel
        """

        obj.save()
        if change:  # only trigger when an object has been changed
            HistoryLogService.log_update(instance=obj, user=request.user)

    def download_csv(self, request, queryset):
        """
        Download a CSV file containing the selected categories
        """
        now = timezone.localtime(timezone.now())
        filename = 'category-report-{}.csv'.format(now.strftime('%Y%m%d_%H%M'))

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}'.format(filename)

        writer = csv.writer(response, delimiter=';', quotechar='"', escapechar='"')

        column_headers = ['parent_name', 'name', 'public name', 'is public accessible', 'slug', 'description',
                          'is active', 'note', 'responsible departments', ]
        writer.writerow(column_headers)

        for category in queryset:
            writer.writerow([
                category.parent.name if category.parent else '',
                category.name,
                category.public_name,
                'Yes' if category.is_public_accessible else 'No',
                category.slug,
                category.description,
                'Yes' if category.is_active else 'No',
                category.note,
                ', '.join([department.name
                           for department in category.departments.filter(categorydepartment__is_responsible=True)]),
            ])

        self.message_user(request, 'Created Category CSV file: {}'.format(filename))
        return response


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

    actions = ['download_csv']

    def download_csv(self, request, queryset):
        """
        Download a CSV file containing the selected status message templates
        """
        now = timezone.localtime(timezone.now())
        filename = 'status-message-template-report-{}.csv'.format(now.strftime('%Y%m%d_%H%M'))

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}'.format(filename)

        writer = csv.writer(response, delimiter=';', quotechar='"', escapechar='"')

        column_headers = ['parent category name', 'category name', 'state', 'title', 'text', 'is_active']
        writer.writerow(column_headers)

        for status_message_template in queryset:
            writer.writerow([
                status_message_template.category.parent.name if status_message_template.category.parent else '',
                status_message_template.category.name,
                status_message_template.get_state_display(),
                status_message_template.title,
                status_message_template.text,
                'Yes' if status_message_template.is_active else 'No'
            ])

        self.message_user(request, 'Created Status message template CSV file: {}'.format(filename))
        return response
