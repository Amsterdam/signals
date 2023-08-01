# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from pytest_bdd import parsers, then, when
from rest_framework.response import Response
from rest_framework.test import APIClient

from signals.apps.signals.models import Signal
from signals.apps.users.models import User


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
