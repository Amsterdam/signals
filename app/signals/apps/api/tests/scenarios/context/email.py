# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
import typing

from django.core import mail
from pytest_bdd import given, parsers, then

from signals.apps.email_integrations.factories import EmailTemplateFactory
from signals.apps.email_integrations.models import EmailTemplate

TEMPLATES: typing.Final = {
    EmailTemplate.NOTIFY_CURRENT_REPORTER: """Beste melder,

Er is een wijziging van uw contact gegevens aangevraagd. Mocht dat niet correct zijn of heeft u deze wijziging niet aangevraagd,
neem dan z.s.m. contact met ons op.

Indien dit wel correct is, gebruik dan de link die wij u naar uw nieuwe e-mailadres hebben verstuurd om uw nieuwe e-mailadres te bevestigen.

Met vriendelijke groet,

{{ ORGANIZATION_NAME }}""", # noqa
    EmailTemplate.VERIFY_EMAIL_REPORTER: """Beste melder,

Er is een wijziging van uw e-mailadres aangevraagd. Graag willen wij u vragen om onderstaande url te gebruiken om uw nieuwe e-mailadres te bevestigen.

[{{ verification_url }}]({{ verification_url }})

Alvast bedankt!

Met vriendelijke groet,

{{ ORGANIZATION_NAME }}""", # noqa
    EmailTemplate.CONFIRM_REPORTER_UPDATED: """Beste melder,

Bij deze bevestigen wij dat uw verzoek om uw contact gegevens te wijzigen succesvol is uitgevoerd.

Met vriendelijke groet,

{{ ORGANIZATION_NAME }}""" # noqa
}


@given(parsers.parse('there is an email template with key {key}'))
def given_email_template(key: str) -> None:
    EmailTemplateFactory.create(key=key, title=key, body=TEMPLATES.get(key))


@then(parsers.parse('the reporter with email address {email} should receive an email with template key {key}'))
def then_email(email: str, key: str) -> None:
    found = False
    for outbox_email in mail.outbox:
        if outbox_email.to[0] == email and outbox_email.subject == key:
            found = True
            break

    assert found
