# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.contrib import admin, messages
from django.contrib.gis.db.models import JSONField
from django.utils.html import format_html
from rest_framework.reverse import reverse

from signals.apps.questionnaires.forms.widgets import PrettyJSONWidget
from signals.apps.questionnaires.models import Question, Questionnaire, Session


class QuestionAdmin(admin.ModelAdmin):
    fields = ('key', 'uuid', 'field_type', 'payload', 'required', 'root', 'created_at',)
    readonly_fields = ('uuid', 'created_at',)
    raw_id_fields = ('root',)

    list_display = ('key', 'uuid', 'field_type', 'created_at',)
    list_per_page = 20
    list_select_related = True

    ordering = ('-created_at',)

    formfield_overrides = {
        JSONField: {'widget': PrettyJSONWidget}
    }


admin.site.register(Question, QuestionAdmin)


class QuestionnaireAdmin(admin.ModelAdmin):
    fields = ('uuid', 'name', 'description', 'first_question', 'is_active', 'created_at',)
    readonly_fields = ('uuid', 'created_at',)
    raw_id_fields = ('first_question',)

    list_display = ('name', 'uuid', 'created_at',)
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


admin.site.register(Session, SessionAdmin)
