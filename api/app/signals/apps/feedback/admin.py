"""
Allow standard feedback answers to be managed through Django Admin.
"""
from django.contrib import admin

from signals.apps.feedback.models import StandardAnswer


class StandardAnswerAdmin(admin.ModelAdmin):
    fields = ('is_satisfied', 'text', 'is_visible')


admin.site.register(StandardAnswer, StandardAnswerAdmin)
