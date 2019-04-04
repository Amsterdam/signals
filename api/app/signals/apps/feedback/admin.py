"""
Allow standard feedback answers to be managed through Django Admin.
"""
from django.contrib import admin

from signals.apps.feedback.models import Feedback, StandardAnswer


class StandardAnswerAdmin(admin.ModelAdmin):
    fields = ('is_satisfied', 'text')


admin.site.register(StandardAnswer, StandardAnswerAdmin)
