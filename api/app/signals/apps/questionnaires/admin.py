# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.contrib import admin

from signals.apps.questionnaires.models import Question, Questionnaire, Session


class QuestionAdmin(admin.ModelAdmin):
    fields = ('key', 'uuid', 'field_type', 'payload', 'required', 'created_at',)
    readonly_fields = ('uuid', 'created_at',)
    list_display = ('key', 'uuid', 'field_type', 'created_at',)
    ordering = ('-created_at',)
    list_per_page = 20
    list_select_related = True


admin.site.register(Question, QuestionAdmin)


class QuestionnaireAdmin(admin.ModelAdmin):
    fields = ('uuid', 'first_question', 'created_at',)
    readonly_fields = ('uuid', 'created_at',)
    list_display = ('uuid', 'created_at',)
    ordering = ('-created_at',)
    list_per_page = 20
    list_select_related = True


admin.site.register(Questionnaire, QuestionnaireAdmin)


class SessionAdmin(admin.ModelAdmin):
    fields = ('uuid', 'started_at', 'submit_before', 'duration', 'created_at',)
    readonly_fields = ('uuid', 'started_at', 'submit_before', 'duration', 'created_at',)
    list_display = ('uuid', 'started_at', 'submit_before', 'created_at',)
    ordering = ('-created_at',)
    list_per_page = 20
    list_select_related = True

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Session, SessionAdmin)
