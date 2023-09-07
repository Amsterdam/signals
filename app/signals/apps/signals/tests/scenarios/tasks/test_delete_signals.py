# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
import pytest
from django.test import override_settings
from pytest_bdd import scenario

from signals.settings import FEATURE_FLAGS

from signals.apps.signals.tests.scenarios.context.signals import * # noqa
from signals.apps.signals.tests.scenarios.context.domain_signals_delete import * # noqa


@pytest.mark.django_db()
@override_settings(
    FEATURE_FLAGS={
        **FEATURE_FLAGS,
        'DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED': True,
    }
)
@scenario(
    'features/delete_signals.feature',
    'Delete a Signal in the state Afgehandeld for x years',
    features_base_dir='./signals/apps/signals/tests/scenarios',
)
def test_delete_signal_afgehandeld():
    pass


@pytest.mark.django_db()
@override_settings(
    FEATURE_FLAGS={
        **FEATURE_FLAGS,
        'DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED': True,
    }
)
@scenario(
    'features/delete_signals.feature',
    'Delete all Signals in the state Afgehandeld for x years',
    features_base_dir='./signals/apps/signals/tests/scenarios',
)
def test_delete_all_signals_afgehandeld():
    pass


@pytest.mark.django_db()
@override_settings(
    FEATURE_FLAGS={
        **FEATURE_FLAGS,
        'DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED': True,
    }
)
@scenario(
    'features/delete_signals.feature',
    'Delete a Signal in the state Geannuleerd for x years',
    features_base_dir='./signals/apps/signals/tests/scenarios',
)
def test_delete_signal_geannuleerd():
    pass


@pytest.mark.django_db()
@override_settings(
    FEATURE_FLAGS={
        **FEATURE_FLAGS,
        'DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED': True,
    }
)
@scenario(
    'features/delete_signals.feature',
    'Delete all Signals in the state Geannuleerd for x years',
    features_base_dir='./signals/apps/signals/tests/scenarios',
)
def test_delete_all_signals_geannuleerd():
    pass


@pytest.mark.django_db()
@override_settings(
    FEATURE_FLAGS={
        **FEATURE_FLAGS,
        'DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED': True,
    }
)
@scenario(
    'features/delete_signals.feature',
    'Delete a Signal in the state Gesplitst for x years',
    features_base_dir='./signals/apps/signals/tests/scenarios',
)
def test_delete_signal_gesplitst():
    pass


@pytest.mark.django_db()
@override_settings(
    FEATURE_FLAGS={
        **FEATURE_FLAGS,
        'DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED': True,
    }
)
@scenario(
    'features/delete_signals.feature',
    'Delete all Signals in the state Gesplitst for x years',
    features_base_dir='./signals/apps/signals/tests/scenarios',
)
def test_delete_all_signals_gesplitst():
    pass
