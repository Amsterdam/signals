# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from django.template import Context, Template, loader

from signals.apps.email_integrations.models import EmailTemplate


class EmailTemplateRenderer:
    def __call__(self, key: str, context: dict) -> tuple[str, str, str]:
        email_template = EmailTemplate.objects.get(key=key)

        rendered_context = {
            'subject': Template(email_template.title).render(Context(context)),
            'body': Template(email_template.body).render(Context(context, autoescape=False))
        }

        subject = Template(email_template.title).render(Context(context, autoescape=False))
        message = loader.get_template('email/_base.txt').render(rendered_context)
        html_message = loader.get_template('email/_base.html').render(rendered_context)

        return subject, message, html_message
