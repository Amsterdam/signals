# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
import typing

import pytest
from django.contrib.auth.models import Permission
from django.core import mail
from pytest_bdd import given, parsers, scenario, then, when
from rest_framework.response import Response
from rest_framework.test import APIClient

from signals.apps.email_integrations.factories import EmailTemplateFactory
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.signals.factories import SignalFactory
from signals.apps.signals.models import Reporter, Signal
from signals.apps.users.factories import GroupFactory, UserFactory
from signals.apps.users.models import User

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


@pytest.mark.django_db()
@scenario(
    'features/update_signal_reporters.feature',
    'Update reporter phone and email of signal with reporter that has phone and email',
    features_base_dir='./signals/apps/api'
)
def test_update_reporter_phone_and_email_of_signal_with_reporter_that_has_phone_and_email():
    """Update reporter phone and email of signal with reporter that has phone and email."""


@pytest.fixture
def api_client():
    return APIClient()


@given('there is a read write user', target_fixture='read_write_user')
def given_read_write_user() -> User:
    user = UserFactory.create(
        first_name='SIA-READ-WRITE',
        last_name='User',
    )
    user.user_permissions.add(Permission.objects.get(codename='sia_read'))
    user.user_permissions.add(Permission.objects.get(codename='sia_write'))
    user.user_permissions.add(Permission.objects.get(codename='sia_can_view_all_categories'))

    permissions = Permission.objects.filter(codename__in=(
        'sia_signal_create_initial',
        'sia_signal_create_note',
        'sia_signal_change_status',
        'sia_signal_change_category'
    ))
    sia_test_group = GroupFactory.create(name='Test Group')
    sia_test_group.permissions.add(*permissions)
    user.groups.add(sia_test_group)

    return user


@given(parsers.parse('there is an email template with key {key}'))
def given_email_template(key: str) -> None:
    EmailTemplateFactory.create(key=key, title=key, body=TEMPLATES.get(key))


@given(
    parsers.parse('there is a signal with reporter phone number {phone} and email address {email}'),
    target_fixture='signal',
)
def given_signal_reporter(phone: str, email: str) -> Signal:
    return SignalFactory.create(
        reporter__phone=phone,
        reporter__email=email,
        reporter__state=Reporter.REPORTER_STATE_APPROVED
    )


@when(
    parsers.parse('I create a new reporter for the signal with phone number {phone} and email address {email}'),
    target_fixture='response',
)
def create_reporter(
        phone: str,
        email: str,
        signal: Signal,
        read_write_user: User,
        api_client: APIClient
) -> Response:
    api_client.force_authenticate(read_write_user)

    return api_client.post(
        f'/signals/v1/private/signals/{signal.id}/reporters/',
        data={'phone': phone, 'email': email, 'sharing_allowed': True},
        format='json',
    )


@then(parsers.parse('the response status code should be {status_code:d}'))
def then_status_code(status_code: int, response: Response) -> None:
    assert response.status_code == status_code


@then(parsers.parse('the reporter with email address {email} should receive an email with template key {key}'))
def then_email(email: str, key: str) -> None:
    found = False
    for outbox_email in mail.outbox:
        if outbox_email.to[0] == email and outbox_email.subject == key:
            found = True
            break

    assert found


@when(parsers.parse('I verify the token of {email}'), target_fixture='response')
def verify_token(email: str, signal: Signal, api_client: APIClient) -> Response:
    reporter = signal.reporters.get(email=email)

    return api_client.post(
        '/signals/v1/public/reporter/verify-email',
        data={'token': reporter.email_verification_token},
        format='json'
    )


@then(parsers.parse('the reporter of the signal should have phone number {phone} and email address {email}'))
def then_signal_updated(phone: str, email: str, signal: Signal) -> None:
    signal.refresh_from_db()
    assert signal.reporter.phone == phone
    assert signal.reporter.email == email
