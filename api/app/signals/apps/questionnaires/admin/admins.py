# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.contrib import admin, messages
from django.utils.html import format_html
from rest_framework.reverse import reverse

from signals.apps.questionnaires.admin.inlines import EdgeStackedInline


class QuestionnaireAdmin(admin.ModelAdmin):
    inlines = (EdgeStackedInline, )
    fieldsets = (
        (None, {'fields': ('uuid', 'created_at',)}),
        ('Details', {'fields': ('name', 'description', 'flow', 'is_active',)}),
        ('Question Graph', {'fields': ('graph',)}),
    )
    readonly_fields = ('uuid', 'created_at',)

    list_display = ('name', 'uuid', 'is_active', 'created_at',)
    list_display_links = ('name', 'uuid',)
    list_filter = ('is_active',)
    list_per_page = 20
    list_select_related = True

    search_fields = ('name',)

    ordering = ('-created_at',)


class QuestionGraphAdmin(admin.ModelAdmin):
    inlines = (EdgeStackedInline,)
    fields = ('name', 'first_question',)

    list_display = ('name', 'first_question',)
    list_per_page = 20


class QuestionAdmin(admin.ModelAdmin):
    fields = ('retrieval_key', 'analysis_key', 'uuid', 'label', 'short_label', 'field_type', 'required', 'created_at',)
    readonly_fields = ('uuid', 'created_at',)

    list_display = ('retrieval_key', 'analysis_key', 'uuid', 'field_type', 'created_at',)
    list_per_page = 20
    list_select_related = True

    ordering = ('-created_at',)


class SessionAdmin(admin.ModelAdmin):
    fields = ('uuid', 'questionnaire', '_signal', 'started_at', 'duration', 'submit_before', 'frozen', 'created_at',)
    readonly_fields = ('uuid', 'started_at', 'frozen', 'created_at',)
    raw_id_fields = ('questionnaire', '_signal',)
    search_fields = ('uuid__startswith',)

    list_display = ('uuid', 'view_questionnaire_link', 'started_at', 'submit_before', 'frozen', 'too_late',)
    list_filter = ('frozen',)
    list_per_page = 20
    list_select_related = True

    actions = ('freeze', 'unfreeze',)

    ordering = ('-created_at',)

    def has_delete_permission(self, request, obj=None):
        if obj and not obj.started_at:
            return True
        return False

    def view_questionnaire_link(self, obj):
        url = reverse('admin:questionnaires_questionnaire_change', kwargs={'object_id': obj.questionnaire.pk})
        return format_html('<a href="{}">{}</a>', url, obj.questionnaire.uuid)
    view_questionnaire_link.short_description = "Questionnaire"

    def view_signal_link(self, obj):
        url = reverse('admin:signals_signal_change', kwargs={'object_id': obj._signal.pk})
        return format_html('<a href="{}">{}</a>', url, obj._signal.sia_id)
    view_signal_link.short_description = "Signal"

    def too_late(self, obj):
        return obj.too_late
    too_late.boolean = True

    def freeze(self, request, queryset):
        if not request.user.has_perm('questionnaires.change_session'):
            messages.add_message(request, messages.ERROR, 'You have no permission to freeze Sessions')
            return

        total_count = queryset.count()
        frozen_pre_count = queryset.filter(frozen=True).count()
        if total_count == frozen_pre_count:
            messages.add_message(request, messages.WARNING, 'All selected Session objects are already frozen')
            return

        queryset.exclude(frozen=True).update(frozen=True)

        frozen_post_count = queryset.filter(frozen=True).count()
        messages.add_message(request, messages.SUCCESS, f'{frozen_post_count-frozen_pre_count} Sessions frozen')

    def unfreeze(self, request, queryset):
        if not request.user.has_perm('questionnaires.change_session'):
            messages.add_message(request, messages.ERROR, 'You have no permission to freeze Sessions')
            return

        total_count = queryset.count()
        not_frozen_pre_count = queryset.filter(frozen=False).count()
        if total_count == not_frozen_pre_count:
            messages.add_message(request, messages.WARNING, 'All selected Session objects are already not frozen')
            return

        queryset.update(frozen=False)

        unfrozen_post_count = queryset.filter(frozen=False).count()
        messages.add_message(request, messages.SUCCESS, f'{unfrozen_post_count-not_frozen_pre_count} Sessions unfrozen')
