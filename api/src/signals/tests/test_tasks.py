from unittest import mock

from django.test import TestCase

from signals.tasks import email_apptimize
from signals.tests.factories import SignalFactory


class TestTaskSendToApptimize(TestCase):

    def test_send_to_apptimize(self):
        pass

    @mock.patch('signals.tasks.send_mail')
    @mock.patch('signals.tasks.log')
    def test_send_to_apptimize_no_signal_found(self,
                                               mocked_log,
                                               mocked_send_mail):
        email_apptimize(id=1)  # id `1` shouldn't be found.
        mocked_log.exception.assert_called_once()
        mocked_send_mail.assert_not_called()

    def test_send_to_apptimize_not_applicable(self):
        pass

    def test_is_signal_applicable_for_apptimize_true(self):
        pass

    def test_is_signal_applicable_for_apptimize_false(self):
        pass
