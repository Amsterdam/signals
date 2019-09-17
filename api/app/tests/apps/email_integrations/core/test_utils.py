from datetime import time
from unittest import mock

from django.test import TestCase

from signals.apps.email_integrations.core.utils import (
    create_default_notification_message,
    is_business_hour
)
from tests.apps.signals.factories import SignalFactory


class TestUtils(TestCase):
    def test_create_default_notification_message_integration_test(self):
        signal = SignalFactory.create()

        message = create_default_notification_message(signal)

        self.assertIn(str(signal.id), message)
        self.assertIn(signal.text, message)

    @mock.patch('signals.apps.email_integrations.core.utils.loader', autospec=True)
    def test_create_default_notification_message(self, mocked_loader):
        # Setting up template mocking.
        mocked_rendered_template = mock.Mock()
        mocked_template = mock.Mock()
        mocked_template.render.return_value = mocked_rendered_template
        mocked_loader.get_template.return_value = mocked_template

        signal = SignalFactory.create()
        message = create_default_notification_message(signal)

        self.assertEqual(message, mocked_rendered_template)
        mocked_loader.get_template.assert_called_once_with('email/default_notification_message.txt')
        mocked_template.render.assert_called_once_with({'signal': signal})

    def test_is_business_hour(self):
        # Assertions for is given time a business hour.
        self.assertEqual(is_business_hour(time(9, 0)), True)
        self.assertEqual(is_business_hour(time(9, 1)), True)
        self.assertEqual(is_business_hour(time(14, 33)), True)
        self.assertEqual(is_business_hour(time(16, 59)), True)
        self.assertEqual(is_business_hour(time(17, 00)), True)

        # Assertions for is given time *not* a business hour.
        self.assertEqual(is_business_hour(time(8, 59)), False)
        self.assertEqual(is_business_hour(time(17, 1)), False)
        self.assertEqual(is_business_hour(time(0, 23)), False)
