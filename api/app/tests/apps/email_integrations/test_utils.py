from unittest import mock

from django.test import TestCase

from signals.apps.email_integrations.utils import create_default_notification_message
from tests.apps.signals.factories import SignalFactory


class TestUtils(TestCase):

    def test_create_default_notification_message_integration_test(self):
        signal = SignalFactory.create()

        message = create_default_notification_message(signal)

        self.assertIn(str(signal.signal_id), message)
        self.assertIn(signal.text, message)

    @mock.patch('signals.apps.email_integrations.utils.loader', autospec=True)
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
