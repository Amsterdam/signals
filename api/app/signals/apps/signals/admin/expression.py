# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.contrib import admin, messages

from signals.apps.dsl.ExpressionEvaluator import ExpressionEvaluator


class RoutingExpressionAdmin(admin.ModelAdmin):
    list_filter = ['_expression___type__name', '_department__code']
    list_display = ['_expression', '_department', 'is_active']

    def save_model(self, request, obj, form, change):
        # if is_active is true, try to compile code, deactivate when invalid
        try:
            if obj.is_active:
                expr = form.cleaned_data.get('_expression', None)
                if expr:
                    ExpressionEvaluator().compile(expr.code)
        except Exception as e:
            obj.is_active = False
            messages.add_message(request, messages.WARNING, f'Rule deactivated due to error in expression: {str(e)}')

        super().save_model(request, obj, form, change)


class ExpressionAdmin(admin.ModelAdmin):
    list_filter = ['_type__name']
    list_display = ['name', 'code', '_type']


class ExpressionTypeAdmin(admin.ModelAdmin):
    pass


class ExpressionContextAdmin(admin.ModelAdmin):
    list_filter = ['_type__name']
