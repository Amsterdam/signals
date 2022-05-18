# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2022 Gemeente Amsterdam

from django.test import TestCase

from signals.apps.api.serializers.nested import _NestedReporterModelSerializer
from signals.apps.signals.factories import ReporterFactory, SignalFactory


class TestReporterSerializer(TestCase):

    serializer = _NestedReporterModelSerializer

    def setUp(self) -> None:
        self.signal = SignalFactory()
        self.reporter = ReporterFactory(
            _signal=self.signal,
            email='fakeText@example.com',
            email_anonymized=False,
            phone_anonymized=False,
        )

    def test_serialize(self):
        """
        Test the serializer
        No rights
        """
        data = self.serializer().to_representation(self.reporter)
        for key in ['email', 'phone', 'sharing_allowed', 'allows_contact']:
            self.assertIn(key, data)
