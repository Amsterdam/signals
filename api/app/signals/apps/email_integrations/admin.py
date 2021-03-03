# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
import json
import os

from django import forms
from django.conf import settings
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.template import Context, Template

from signals.apps.email_integrations.models import EmailTemplate


class EmailTemplateAdminForm(forms.ModelForm):
    default_error_message = 'Er heeft zich een fout voorgedaan bij het valideren van de data.'

    class Meta:
        model = EmailTemplate
        exclude = ('created_by', )

    _dummy_signal = None

    @property
    def dummy_signal(self):
        """
        Will convert the dummy signal json to a "DummyObject" that can be used in the template and template tags
        TODO: Think about data we want to expose to the email templates instead of just exposing the whole Signal.
        """
        if not self._dummy_signal:
            class DummyObject(object):
                # This will make sure the Json is accessible as an "object", for example x.y instead of x['y']
                def __init__(self, d):
                    for a, b in d.items():
                        if isinstance(b, (list, tuple)):
                            setattr(self, a, [DummyObject(x) if isinstance(x, dict) else x for x in b])
                        else:
                            setattr(self, a, DummyObject(b) if isinstance(b, dict) else b)

            # Load a fixture file with a JSON dump of a dummy signal
            filename = os.path.join(os.path.dirname(__file__), 'dummy_data', 'dummy_signal.json')
            with open(filename) as f:
                self._dummy_signal = DummyObject(json.load(f))

        return self._dummy_signal

    def _validate_template_syntax(self, template_data):
        """
        This function tries to catch any invalid Django template syntax and raise a ValidationError.
        Additional debug data is added to the error if the DEBUG setting is set to True
        """
        try:
            engine = None  # This will result in the default behaviour
            if settings.DEBUG:
                # We want to have a bit more debug information available
                from django.template import Engine
                engine = Engine.get_default()
                engine.debug = True

            Template(template_data, engine=engine)
        except Exception as e:
            error_message = self.default_error_message
            if settings.DEBUG:  # Adding debug information to the error
                error_message = f'{self.default_error_message}. Debug information (DEBUG=True): {e.template_debug}'
            raise ValidationError(error_message)

    def _validate_template_rendering(self, template_data, autoescape=True):
        """
        This function tries to catch any errors when rendering the template and raise a ValidationError.
        Additional debug data is added to the error if the DEBUG setting is set to True
        """
        try:
            context = Context(dict(signal=self.dummy_signal), autoescape=autoescape)
            Template(template_data).render(context=context)
        except Exception as e:
            error_message = self.default_error_message
            if settings.DEBUG:  # Adding debug information to the error
                error_message = f'{self.default_error_message}. Debug information (DEBUG=True): {e.template_debug}'
            raise ValidationError(error_message)

    def clean_title(self):
        self._validate_template_syntax(template_data=self.cleaned_data['title'])
        self._validate_template_rendering(template_data=self.cleaned_data['title'])

        return self.cleaned_data['title']

    def clean_body(self):
        self._validate_template_syntax(template_data=self.cleaned_data['body'])
        self._validate_template_rendering(template_data=self.cleaned_data['body'])

        return self.cleaned_data['body']


@admin.register(EmailTemplate)
class EmailTemplate(admin.ModelAdmin):
    list_display = ('key', 'title', )
    readonly_fields = ('created_by', )
    form = EmailTemplateAdminForm

    def save_model(self, request, obj, form, change):
        obj.created_by = request.user.email
        super().save_model(request, obj, form, change)
