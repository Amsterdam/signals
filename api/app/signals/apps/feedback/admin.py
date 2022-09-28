# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2022 Gemeente Amsterdam
"""
Allow standard feedback answers to be managed through Django Admin.
"""
from django.contrib import admin

from signals.apps.feedback.models import StandardAnswer, StandardAnswerTopic


class StandardAnswerAdmin(admin.ModelAdmin):
    list_display = ('pos_or_neg', 'text', 'is_visible',
                    'reopens_when_unhappy', 'topic', 'order')
    list_display_links = list_display

    def pos_or_neg(self, obj):
        if obj.is_satisfied:
            return 'POSITIEF'
        return 'NEGATIEF'


class StandardAnswerTopicAdmin(admin.ModelAdmin):
    list_display = ('description', 'text', 'order')
    list_display_links = list_display


admin.site.register(StandardAnswer, StandardAnswerAdmin)
admin.site.register(StandardAnswerTopic, StandardAnswerTopicAdmin)
