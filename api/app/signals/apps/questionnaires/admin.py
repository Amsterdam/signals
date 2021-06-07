# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.contrib import admin, messages
from django.utils import timezone
from django.utils.html import format_html
from rest_framework.reverse import reverse

from signals.apps.questionnaires.models import Question, Questionnaire, Session


class QuestionAdmin(admin.ModelAdmin):
    fields = ('key', 'uuid', 'field_type', 'payload', 'required', 'root', 'created_at',)
    readonly_fields = ('uuid', 'created_at',)
    raw_id_fields = ('root',)

    list_display = ('key', 'uuid', 'field_type', 'created_at',)
    list_per_page = 20
    list_select_related = True

    ordering = ('-created_at',)


admin.site.register(Question, QuestionAdmin)


class QuestionnaireAdmin(admin.ModelAdmin):
    fields = ('uuid', 'first_question', 'created_at',)
    readonly_fields = ('uuid', 'created_at',)
    raw_id_fields = ('first_question',)

    list_display = ('uuid', 'created_at',)
    list_per_page = 20
    list_select_related = True

    ordering = ('-created_at',)


admin.site.register(Questionnaire, QuestionnaireAdmin)


class SessionAdmin(admin.ModelAdmin):
    fields = ('uuid', 'questionnaire', 'started_at', 'duration', 'submit_before', 'frozen', 'created_at',)
    readonly_fields = ('uuid', 'started_at', 'frozen', 'created_at',)
    raw_id_fields = ('questionnaire',)
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

    def too_late(self, obj):
        now = timezone.now()
        return (
            not obj.frozen and (
                (obj.submit_before and obj.submit_before < now) or
                (obj.started_at and obj.started_at + obj.duration < now)
            )
        )
    too_late.boolean = True

    def freeze(self, request, queryset):
        if request.user.has_perm('questionnaires.change_session') and queryset.filter(frozen=False).exists():
            queryset.update(frozen=True)
            messages.add_message(request, messages.SUCCESS, 'Sessions frozen')
        elif request.user.has_perm('questionnaires.change_session') and not queryset.filter(frozen=False).exists():
            messages.add_message(request, messages.WARNING, 'All selected Sessions are already frozen')
        else:
            messages.add_message(request, messages.ERROR, 'You have no permission to freeze Sessions')

    def unfreeze(self, request, queryset):
        if request.user.has_perm('questionnaires.change_session') and queryset.filter(frozen=True).exists():
            queryset.update(frozen=False)
            messages.add_message(request, messages.SUCCESS, 'Sessions unfrozen')
        elif request.user.has_perm('questionnaires.change_session') and not queryset.filter(frozen=True).exists():
            messages.add_message(request, messages.WARNING, 'All selected Sessions are not frozen')
        else:
            messages.add_message(request, messages.ERROR, 'You have no permission to unfreeze Sessions')


admin.site.register(Session, SessionAdmin)
