"""
Allow standard feedback answers to be managed through Django Admin.
"""
from django.contrib import admin

from signals.apps.feedback.models import StandardAnswer


class StandardAnswerAdmin(admin.ModelAdmin):
    pass
admin.site.register(StandardAnswer, StandardAnswerAdmin)
