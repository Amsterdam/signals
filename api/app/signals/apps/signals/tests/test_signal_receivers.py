# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Delta10 B.V.
from unittest import mock

from django.test import TestCase, override_settings

from signals.apps.signals.factories import SignalFactory
from signals.apps.signals.managers import (
    create_initial,
    update_category_assignment,
    update_location
)


@override_settings(FEATURE_FLAGS={'DSL_RUN_ROUTING_EXPRESSIONS_ON_UPDATES': True})
class TestSignalsSignalReceivers(TestCase):
    def setUp(self):
        self.signal = SignalFactory.create()

    @mock.patch('signals.apps.signals.signal_receivers.tasks', autospec=True)
    def test_signals_create_initial_handler(self, mocked_tasks):
        create_initial.send_robust(
            sender=self.__class__,
            signal_obj=self.signal,
        )

        mocked_tasks.apply_routing.delay.assert_called_once_with(
            self.signal.id
        )

    @mock.patch('signals.apps.signals.signal_receivers.tasks', autospec=True)
    def test_signals_update_location_handler(self, mocked_tasks):
        update_location.send_robust(
            sender=self.__class__,
            signal_obj=self.signal,
        )

        mocked_tasks.apply_routing.delay.assert_called_once_with(
            self.signal.id
        )

    @mock.patch('signals.apps.signals.signal_receivers.tasks', autospec=True)
    def test_signals_update_category_assignment_handler(self, mocked_tasks):
        update_category_assignment.send_robust(
            sender=self.__class__,
            signal_obj=self.signal,
        )

        mocked_tasks.apply_routing.delay.assert_called_once_with(
            self.signal.id
        )
