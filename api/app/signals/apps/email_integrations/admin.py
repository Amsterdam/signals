from django.contrib import admin

from .models import EmailTemplate


@admin.register(EmailTemplate)
class EmailTemplate(admin.ModelAdmin):
    list_display = ('key', 'title')
    readonly_fields = ('created_by',)

    def save_model(self, request, obj, form, change):
        obj.created_by = request.user.email
        super().save_model(request, obj, form, change)
