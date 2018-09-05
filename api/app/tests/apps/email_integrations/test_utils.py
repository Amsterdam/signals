from datetime import datetime
from unittest import mock

from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time

from signals.apps.email_integrations.utils import (
    create_default_notification_message,
    is_now_business_hour
)
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

    def test_is_now_business_hour(self):
        utcoffset = timezone.localtime(timezone.now()).utcoffset()
        time_0859 = datetime(2018, 9, 5, 8, 59) - utcoffset
        time_0900 = datetime(2018, 9, 5, 9, 0) - utcoffset
        time_0901 = datetime(2018, 9, 5, 9, 1) - utcoffset
        time_1433 = datetime(2018, 9, 5, 14, 33) - utcoffset
        time_1659 = datetime(2018, 9, 5, 16, 59) - utcoffset
        time_1700 = datetime(2018, 9, 5, 17, 0) - utcoffset
        time_1701 = datetime(2018, 9, 5, 17, 1) - utcoffset
        time_0023 = datetime(2018, 9, 5, 0, 23) - utcoffset

        # Assertion for now is business hour.
        with freeze_time(time_0900):
            self.assertEqual(is_now_business_hour(), True, 'Time: 09:00:00')
        with freeze_time(time_0901):
            self.assertEqual(is_now_business_hour(), True, 'Time: 09:01:00')
        with freeze_time(time_1433):
            self.assertEqual(is_now_business_hour(), True, 'Time: 14:33:00')
        with freeze_time(time_1659):
            self.assertEqual(is_now_business_hour(), True, 'Time: 16:59:00')
        with freeze_time(time_1700):
            self.assertEqual(is_now_business_hour(), True, 'Time: 17:00:00')

        # Assertion for now is not business hour.
        with freeze_time(time_0859):
            self.assertEqual(is_now_business_hour(), False, 'Time: 08:59:00')
        with freeze_time(time_1701):
            self.assertEqual(is_now_business_hour(), False, 'Time: 17:01:00')
        with freeze_time(time_0023):
            self.assertEqual(is_now_business_hour(), False, 'Time: 00:23:00')
