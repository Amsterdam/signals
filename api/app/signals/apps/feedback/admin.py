"""
Allow standard feedback answers to be managed through Django Admin.
"""
from django.contrib import admin

from signals.apps.feedback.models import Feedback, StandardAnswer


class StandardAnswerAdmin(admin.ModelAdmin):
    fields = ('is_satisfied', 'text')


class FeedbackAdmin(admin.ModelAdmin):
    fields = ('token', '_signal', 'is_satisfied', 'allows_contact', 'text', 'text_extra')


admin.site.register(StandardAnswer, StandardAnswerAdmin)
admin.site.register(Feedback, FeedbackAdmin)
