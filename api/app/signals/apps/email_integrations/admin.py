from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.reporter.mail_actions import Context, MailActions, Template
from signals.apps.signals.factories import SignalFactoryValidLocation


class EmailTemplateAdminForm(forms.ModelForm):
    class Meta:
        model = EmailTemplate
        exclude = ('created_by', )

    def _validate_template_rendering(self, data):
        """
        This function will validate if the given data can be rendered as an actual e-mail message or subject
        """
        test_signal = SignalFactoryValidLocation()  # Not stored in the DB only used to provided in the Context
        mail_actions = MailActions()  # noqa Only used to determine the action and get the correct context, will not send any e-mail
        for action in mail_actions._get_actions(signal=test_signal):
            context = mail_actions._get_mail_context(signal=test_signal, mail_kwargs=mail_actions._kwargs[action])

            try:
                Template(data).render(Context(context, autoescape=False))
            except Exception:  # Catch all error's and show a "default" message
                raise ValidationError('Er heeft zich een fout voorgedaan bij het valideren van de gegeven data')

    def clean_title(self):
        self._validate_template_rendering(self.cleaned_data['title'])
        return self.cleaned_data['title']

    def clean_body(self):
        self._validate_template_rendering(self.cleaned_data['body'])
        return self.cleaned_data['body']


@admin.register(EmailTemplate)
class EmailTemplate(admin.ModelAdmin):
    list_display = ('key', 'title', )
    readonly_fields = ('created_by', )
    form = EmailTemplateAdminForm

    def save_model(self, request, obj, form, change):
        obj.created_by = request.user.email
        super().save_model(request, obj, form, change)
