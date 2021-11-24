# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db import models
from markdownx.widgets import AdminMarkdownxWidget

from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.utils import validate_email_template, validate_template


class EmailTemplateAdminForm(forms.ModelForm):
    class Meta:
        model = EmailTemplate
        exclude = ('created_by', )

    def clean_title(self):
        if not validate_template(template=self.cleaned_data['title']):
            raise ValidationError('De titel is niet valide')

        return self.cleaned_data['title']

    def clean_body(self):
        if not validate_template(template=self.cleaned_data['body']):
            raise ValidationError('De body is niet valide')

        return self.cleaned_data['body']


@admin.register(EmailTemplate)
class EmailTemplate(admin.ModelAdmin):
    change_form_template = 'admin/change_email_template_form.html'
    formfield_overrides = {
        models.TextField: {'widget': AdminMarkdownxWidget},
    }

    list_display = ('key', 'title', )
    readonly_fields = ('created_by', )
    form = EmailTemplateAdminForm

    actions = ['validate_templates']

    def validate_templates(self, request, queryset):
        for email_template in queryset.all():
            if validate_email_template(email_template=email_template):
                self.message_user(request, f"De E-mail template '{email_template}', is valide.", messages.SUCCESS)
            else:
                self.message_user(request, f"De E-mail template '{email_template}', is NIET valide.", messages.ERROR)
    validate_templates.short_description = 'Geselecteerde E-mail templates valideren'

    def save_model(self, request, obj, form, change):
        obj.created_by = request.user.email
        super().save_model(request, obj, form, change)
