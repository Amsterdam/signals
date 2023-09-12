# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.contrib import admin


class DeletedSignalAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Signal information', {
            'fields': ('signal_id', 'signal_uuid', 'signal_created_at', 'signal_state', 'signal_state_set_at',
                       'get_category_name',)
        }),
        ('Action information', {
            'fields': ('note', 'action', 'deleted_at', 'get_deleted_by', 'batch_uuid',)
        }),
    )

    date_hierarchy = 'deleted_at'
    list_display = ('signal_id', 'signal_state', 'signal_state_set_at', 'action', 'deleted_at', 'batch_uuid',)
    list_select_related = True
    list_filter = ('action', 'deleted_at', )
    ordering = ('-deleted_at',)

    search_fields = ['signal_id__exact', ]

    @admin.action(description='category')
    def get_category_name(self, obj):
        return obj.category.name

    @admin.action(description='deleted by')
    def get_deleted_by(self, obj):
        return obj.deleted_by or 'Signalen system'

    # No adding, editing or deleting allowed in the admin
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
