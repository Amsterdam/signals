from unittest import mock

from django.test import TestCase


class TestSignalReceivers(TestCase):

    @mock.patch('signals.apps.sigmax.signal_receivers.tasks', autospec=True)
    def test_create_initial_handler(self, mocked_tasks):
        pass
