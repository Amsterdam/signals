# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2025 Delta10 B.V.

from django.contrib import admin
from .forms import ForwardToExternalModelForm, SetStateModelForm
from .models import ForwardToExternal, SetState


class ForwardToExternalAdmin(admin.ModelAdmin):
    form = ForwardToExternalModelForm
    change_form_template = 'admin/change_external_rule_automation_form.html'
    list_display = ['expression', 'email', 'text']


class SetStateAdmin(admin.ModelAdmin):
    form = SetStateModelForm
    change_form_template = 'admin/change_set_state_automation_form.html'
    list_display = ['expression', 'desired_state', 'text']


admin.site.register(ForwardToExternal, ForwardToExternalAdmin)
admin.site.register(SetState, SetStateAdmin)
