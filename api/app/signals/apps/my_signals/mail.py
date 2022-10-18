# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.conf import settings
from django.core.mail import send_mail
from django.template import Context, Template, loader
from django.utils.timezone import now

from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.my_signals.app_settings import MY_SIGNALS_LOGIN_URL
from signals.apps.my_signals.models import Token


def send_token_mail(token: Token) -> int:
    """
    Send an email containing the "My Signals" token to the reporter
    """
    if token.expires_at < now():
        # Given token is expired, do not sent the mail
        return 0

    context = {'login_url': f'{MY_SIGNALS_LOGIN_URL}/{token.key}', 'ORGANIZATION_NAME': settings.ORGANIZATION_NAME}

    try:
        email_template = EmailTemplate.objects.get(key=EmailTemplate.MY_SIGNAL_TOKEN)

        rendered_context = {
            'subject': Template(email_template.title).render(Context(context)),
            'body': Template(email_template.body).render(Context(context, autoescape=False))
        }

        subject = Template(email_template.title).render(Context(context, autoescape=False))
        message = loader.get_template('email/_base.txt').render(rendered_context)
        html_message = loader.get_template('email/_base.html').render(rendered_context)
    except EmailTemplate.DoesNotExist:
        subject = 'My Signals Token'
        message = loader.get_template('email/signal_default.txt').render(context)
        html_message = loader.get_template('email/signal_default.html').render(context)

    return send_mail(subject=subject, message=message, from_email=settings.DEFAULT_FROM_EMAIL,
                     recipient_list=[token.reporter_email, ], html_message=html_message)
