from django.contrib import admin

from signals.apps.signals.models import Category, Text


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


class StatusTextTemplatesAdmin(admin.ModelAdmin):
    list_display = ('category', 'state', 'order', 'text',)
    list_display_links = list_display
    list_filter = (ChildCategoryFilter,)


admin.site.register(Text, StatusTextTemplatesAdmin)
