"""
Allow standard feedback answers to be managed through Django Admin.
"""
from django.contrib import admin

from signals.apps.feedback.models import StandardAnswer


class StandardAnswerAdmin(admin.ModelAdmin):
    list_display = ('pos_or_neg', 'text', 'is_visible', 'reopens_when_unhappy')
    list_display_links = list_display

    def pos_or_neg(self, obj):
        if obj.is_satisfied:
            return 'POSITIEF'
        return 'NEGATIEF'


admin.site.register(StandardAnswer, StandardAnswerAdmin)
