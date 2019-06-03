from django.contrib import admin

from signals.apps.signals.models import Category, StatusMessageTemplate
from signals.apps.signals.models.category_translation import CategoryTranslation


class CategoryTranslationAdmin(admin.ModelAdmin):
    fields = ('old_category', 'new_category', 'text', 'created_by')
    readonly_fields = ('created_by',)

    def save_model(self, request, obj, form, change):
        obj.created_by = request.user.email
        super().save_model(request, obj, form, change)


admin.site.register(CategoryTranslation, CategoryTranslationAdmin)


class ChildCategoryFilter(admin.SimpleListFilter):
    title = 'Child category'
    parameter_name = 'category_id'

    def lookups(self, request, model_admin):
        return [
            (category.pk, category.__str__())
            for category in Category.objects.iterator()
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(category__id=self.value())
        return queryset.all()


class StatusMessageTemplatesAdmin(admin.ModelAdmin):
    list_display = ('category', 'state', 'order', 'text',)
    list_display_links = list_display
    list_filter = (ChildCategoryFilter,)


admin.site.register(StatusMessageTemplate, StatusMessageTemplatesAdmin)
