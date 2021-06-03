# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.contrib import admin

from signals.apps.questionnaires.models import Question, Questionnaire, Session


class QuestionAdmin(admin.ModelAdmin):
    fields = ('key', 'uuid', 'field_type', 'payload', 'required', 'root', 'created_at',)
    readonly_fields = ('uuid', 'created_at',)
    raw_id_fields = ('root',)
    list_display = ('key', 'uuid', 'field_type', 'created_at',)
    ordering = ('-created_at',)
    list_per_page = 20
    list_select_related = True


admin.site.register(Question, QuestionAdmin)


class QuestionnaireAdmin(admin.ModelAdmin):
    fields = ('uuid', 'first_question', 'created_at',)
    readonly_fields = ('uuid', 'created_at',)
    raw_id_fields = ('first_question',)
    list_display = ('uuid', 'created_at',)
    ordering = ('-created_at',)
    list_per_page = 20
    list_select_related = True


admin.site.register(Questionnaire, QuestionnaireAdmin)


class SessionAdmin(admin.ModelAdmin):
    fields = ('uuid', 'questionnaire', 'started_at', 'duration', 'submit_before', 'frozen', 'created_at',)
    readonly_fields = ('uuid', 'started_at', 'frozen', 'created_at',)
    raw_id_fields = ('questionnaire',)
    list_display = ('uuid', 'questionnaire', 'started_at', 'submit_before', 'created_at',)
    ordering = ('-created_at',)
    list_per_page = 20
    list_select_related = True

    def has_delete_permission(self, request, obj=None):
        if obj and not obj.started_at:
            return True
        return False


admin.site.register(Session, SessionAdmin)
