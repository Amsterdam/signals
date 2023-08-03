# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
import pytest
from pytest_bdd import scenario

from signals.apps.api.tests.scenarios.context.api import * # noqa
from signals.apps.api.tests.scenarios.context.email import * # noqa
from signals.apps.api.tests.scenarios.context.reporter import * # noqa
from signals.apps.api.tests.scenarios.context.signal import * # noqa
from signals.apps.api.tests.scenarios.context.user import * # noqa


@pytest.mark.django_db()
@scenario(
    'features/update_signal_reporters.feature',
    'Update reporter phone and email of signal with reporter that has phone and email',
    features_base_dir='./signals/apps/api',
)
def test_update_reporter_phone_and_email_of_signal_with_reporter_that_has_phone_and_email():
    """Update reporter phone and email of signal with reporter that has phone and email."""


@pytest.mark.django_db()
@scenario(
    'features/update_signal_reporters.feature',
    'Update reporter phone and email of signal with reporter that has only phone number',
    features_base_dir='./signals/apps/api',
)
def test_update_reporter_phone_and_email_of_signal_with_reporter_that_has_only_phone_number():
    """Update reporter phone and email of signal with reporter that has only phone number."""


@pytest.mark.django_db()
@scenario(
    'features/update_signal_reporters.feature',
    'Update reporter phone and email of signal with reporter that has only email address',
    features_base_dir='./signals/apps/api',
)
def test_update_reporter_phone_and_email_of_signal_with_reporter_that_has_only_email_address():
    """Update reporter phone and email of signal with reporter that has only email address."""


@pytest.mark.django_db()
@scenario(
    'features/update_signal_reporters.feature',
    'Update reporter phone and email of signal with reporter that has neither',
    features_base_dir='./signals/apps/api',
)
def test_update_reporter_phone_and_email_of_signal_with_reporter_that_has_neither():
    """Update reporter phone and email of signal with reporter that has neither."""


@pytest.mark.django_db()
@scenario(
    'features/update_signal_reporters.feature',
    'Update phone and email of signal with reporter that has new state',
    features_base_dir='./signals/apps/api',
)
def test_update_reporter_phone_and_email_of_signal_with_reporter_that_has_new_state():
    """Update phone and email of signal with reporter that has new state."""


@pytest.mark.django_db()
@scenario(
    'features/update_signal_reporters.feature',
    'Update phone and email of signal with reporter that has verification_email_sent state',
    features_base_dir='./signals/apps/api',
)
def test_update_reporter_phone_and_email_of_signal_with_reporter_that_has_verification_email_sent_state():
    """Update phone and email of signal with reporter that has verification_email_sent state."""


@pytest.mark.django_db()
@scenario(
    'features/update_signal_reporters.feature',
    'Update phone and email of signal with reporter that has cancelled state',
    features_base_dir='./signals/apps/api',
)
def test_update_reporter_phone_and_email_of_signal_with_reporter_that_has_cancelled_state():
    """Update phone and email of signal with reporter that has cancelled state."""


@pytest.mark.django_db()
@scenario(
    'features/update_signal_reporters.feature',
    'Update reporter phone of signal with reporter that has phone and email',
    features_base_dir='./signals/apps/api',
)
def test_update_reporter_phone_of_signal_with_reporter_that_has_phone_and_email():
    """Update reporter phone of signal with reporter that has phone and email."""


@pytest.mark.django_db()
@scenario(
    'features/update_signal_reporters.feature',
    'Update reporter phone of signal with reporter that has only phone',
    features_base_dir='./signals/apps/api',
)
def test_update_reporter_phone_of_signal_with_reporter_that_has_only_phone():
    """Update reporter phone of signal with reporter that has only phone."""


@pytest.mark.django_db()
@scenario(
    'features/update_signal_reporters.feature',
    'Update reporter phone of signal with reporter that has only email',
    features_base_dir='./signals/apps/api',
)
def test_update_reporter_phone_of_signal_with_reporter_that_has_only_email():
    """Update reporter phone of signal with reporter that has only email."""


@pytest.mark.django_db()
@scenario(
    'features/update_signal_reporters.feature',
    'Update reporter phone of signal with reporter that has neither',
    features_base_dir='./signals/apps/api',
)
def test_update_reporter_phone_of_signal_with_reporter_that_has_neither():
    """Update reporter phone of signal with reporter that has neither."""


@pytest.mark.django_db()
@scenario(
    'features/update_signal_reporters.feature',
    'Update phone of signal with reporter that has new state',
    features_base_dir='./signals/apps/api',
)
def test_update_reporter_phone_of_signal_with_reporter_that_has_new_state():
    """Update phone of signal with reporter that has new state."""


@pytest.mark.django_db()
@scenario(
    'features/update_signal_reporters.feature',
    'Update phone of signal with reporter that has verification_email_sent state',
    features_base_dir='./signals/apps/api',
)
def test_update_reporter_phone_of_signal_with_reporter_that_has_verification_email_sent_state():
    """Update phone of signal with reporter that has verification_email_sent state."""


@pytest.mark.django_db()
@scenario(
    'features/update_signal_reporters.feature',
    'Update phone of signal with reporter that has cancelled state',
    features_base_dir='./signals/apps/api',
)
def test_update_reporter_phone_of_signal_with_reporter_that_has_cancelled_state():
    """Update phone of signal with reporter that has cancelled state."""


@pytest.mark.django_db()
@scenario(
    'features/update_signal_reporters.feature',
    'Update reporter email of signal with reporter that has phone and email',
    features_base_dir='./signals/apps/api',
)
def test_update_reporter_email_of_signal_with_reporter_that_has_phone_and_email():
    """Update reporter email of signal with reporter that has phone and email."""


@pytest.mark.django_db()
@scenario(
    'features/update_signal_reporters.feature',
    'Update reporter email of signal with reporter that has only phone',
    features_base_dir='./signals/apps/api',
)
def test_update_reporter_email_of_signal_with_reporter_that_has_only_phone():
    """Update reporter email of signal with reporter that has only phone."""


@pytest.mark.django_db()
@scenario(
    'features/update_signal_reporters.feature',
    'Update reporter email of signal with reporter that has only email',
    features_base_dir='./signals/apps/api',
)
def test_update_reporter_email_of_signal_with_reporter_that_has_only_email():
    """Update reporter email of signal with reporter that has only email."""


@pytest.mark.django_db()
@scenario(
    'features/update_signal_reporters.feature',
    'Update reporter email of signal with reporter that has neither',
    features_base_dir='./signals/apps/api',
)
def test_update_reporter_email_of_signal_with_reporter_that_has_neither():
    """Update reporter email of signal with reporter that has neither."""


@pytest.mark.django_db()
@scenario(
    'features/update_signal_reporters.feature',
    'Update email of signal with reporter that has new state',
    features_base_dir='./signals/apps/api',
)
def test_update_reporter_email_of_signal_with_reporter_that_has_new_state():
    """Update reporter email of signal with reporter that has new state."""


@pytest.mark.django_db()
@scenario(
    'features/update_signal_reporters.feature',
    'Update email of signal with reporter that has verification_email_sent state',
    features_base_dir='./signals/apps/api',
)
def test_update_reporter_email_of_signal_with_reporter_that_has_verification_email_sent_state():
    """Update email of signal with reporter that has verification_email_sent state."""
