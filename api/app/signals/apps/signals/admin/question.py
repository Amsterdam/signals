# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.contrib import admin

from signals.apps.signals.models import CategoryQuestion


class CategoryQuestionInline(admin.StackedInline):
    raw_id_fields = ('category', 'question',)
    model = CategoryQuestion
    extra = 1


class QuestionAdmin(admin.ModelAdmin):
    inlines = (CategoryQuestionInline, )
    fields = ('key', 'field_type', 'meta', 'required')
    list_display = ('key', 'field_type', 'meta', 'required', 'categories')
    ordering = ('-key',)
    list_per_page = 20
    list_select_related = True
    list_filter = ['category__slug']

    def categories(self, obj):
        categories = obj.category_set.values_list('name', flat=True)
        return ', '.join(categories)
