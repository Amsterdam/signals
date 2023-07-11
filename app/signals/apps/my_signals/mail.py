# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 - 2023 Gemeente Amsterdam
from django.conf import settings
from django.core.mail import send_mail
from django.template import loader
from django.utils.timezone import now

from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.renderers.email_template_renderer import EmailTemplateRenderer
from signals.apps.my_signals.app_settings import MY_SIGNALS_URL
from signals.apps.my_signals.models import Token


def send_token_mail(token: Token) -> int:
    """
    Send an email containing the "My Signals" token to the reporter
    """
    if token.expires_at < now():
        # Given token is expired, do not sent the mail
        return 0

    context = {'my_signals_url': f'{MY_SIGNALS_URL}/{token.key}', 'ORGANIZATION_NAME': settings.ORGANIZATION_NAME}

    try:
        render = EmailTemplateRenderer()
        subject, message, html_message = render(EmailTemplate.MY_SIGNAL_TOKEN, context)
    except EmailTemplate.DoesNotExist:
        subject = 'My Signals Token'
        message = loader.get_template('email/signal_default.txt').render(context)
        html_message = loader.get_template('email/signal_default.html').render(context)

    return send_mail(subject=subject, message=message, from_email=settings.DEFAULT_FROM_EMAIL,
                     recipient_list=[token.reporter_email, ], html_message=html_message)
