# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2024 Gemeente Amsterdam
from unittest import mock
from unittest.mock import MagicMock

from django.test import TestCase

from signals.apps.signals.factories import SignalFactory
from signals.apps.signals.models import Signal


class TestSearchSignalReceivers(TestCase):
    _signal: Signal

    def setUp(self) -> None:
        self._signal = SignalFactory.create()

    @mock.patch("signals.apps.search.signal_receivers.save_to_elastic")
    def test_reporter_anonymized_receiver(self, save_to_elastic: MagicMock) -> None:
        assert self._signal.reporter is not None
        self._signal.reporter.anonymize()

        save_to_elastic.delay.assert_called_once_with(signal_id=self._signal.id)
