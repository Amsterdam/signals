# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2025 Delta10 B.V.

from django.contrib import admin
from .forms import ForwardToExternalModelForm
from .models import ForwardToExternal


class ForwardToExternalAdmin(admin.ModelAdmin):
    form = ForwardToExternalModelForm
    change_form_template = 'admin/change_external_rule_automation_form.html'
    list_display = ['expression', 'email', 'text']


admin.site.register(ForwardToExternal, ForwardToExternalAdmin)
