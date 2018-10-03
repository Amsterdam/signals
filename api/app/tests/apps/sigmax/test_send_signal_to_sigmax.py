from unittest import mock

from django.core.management import call_command
from django.test import TestCase, TransactionTestCase, override_settings

REQUIRED_ENV = {'SIGMAX_AUTH_TOKEN': 'TEST', 'SIGMAX_SERVER': 'https://example.com'}


@override_settings(
    SIGMAX_AUTH_TOKEN=REQUIRED_ENV['SIGMAX_AUTH_TOKEN'],
    SIGMAX_SERVER=REQUIRED_ENV['SIGMAX_SERVER']
)
class CommandTestCaseWithoutCelery(TestCase):
    @mock.patch('signals.apps.sigmax.outgoing._stuf_response_ok')
    @mock.patch('requests.post', autospec=True)
    def test_send_signal_to_sigmax_no_celery(self, mocked_request_post, mocked_stuf_response_ok):
        mocked_request_post.return_value.status_code = 200
        mocked_request_post.return_value.text = 'Some text from Sigmax'
        mocked_stuf_response_ok.return_value = True

        call_command('send_signal_to_sigmax_no_celery')

        args, kwargs = mocked_request_post.call_args
        self.assertIn('data', kwargs)
        self.assertEqual(kwargs['verify'], False)
        self.assertEqual(kwargs['url'], REQUIRED_ENV['SIGMAX_SERVER'])
        self.assertEqual(
            kwargs['headers']['Authorization'],
            'Basic ' + REQUIRED_ENV['SIGMAX_AUTH_TOKEN']
        )


@override_settings(
    SIGMAX_AUTH_TOKEN=REQUIRED_ENV['SIGMAX_AUTH_TOKEN'],
    SIGMAX_SERVER=REQUIRED_ENV['SIGMAX_SERVER']
)
class CommandTestCaseWithCelery(TransactionTestCase):
    @mock.patch('signals.apps.sigmax.signal_receivers.tasks', autospec=True)
    def test_send_signal_to_sigmax(self, mocked_tasks):
        call_command('send_signal_to_sigmax')

        mocked_tasks.push_to_sigmax.delay.assert_called_once()