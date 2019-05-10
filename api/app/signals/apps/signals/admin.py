"""
Allow the category translations to be added or removed via the Django Admin.
"""

from django.contrib import admin

from signals.apps.signals.models.category_translation import CategoryTranslation


class CategoryTranslationAdmin(admin.ModelAdmin):
    fields = ('old_category', 'new_category', 'text')
    readonly_fields = ('created_by',)

    def save_model(self, request, obj, form, change):
        obj.created_by = request.user.email
        super().save_model(request, obj, form, change)
