from django.contrib import admin

from .models import EmailTemplate


@admin.register(EmailTemplate)
class EmailTemplate(admin.ModelAdmin):
    list_display = ('key', 'title')
