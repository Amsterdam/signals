from unittest import mock

from django.core.management import call_command
from django.test import TestCase, override_settings

REQUIRED_ENV = {'SIGMAX_AUTH_TOKEN': 'TEST', 'SIGMAX_SERVER': 'https://example.com'}


@override_settings(
    SIGMAX_AUTH_TOKEN=REQUIRED_ENV['SIGMAX_AUTH_TOKEN'],
    SIGMAX_SERVER=REQUIRED_ENV['SIGMAX_SERVER']
)
class CommandTestCase(TestCase):
    @mock.patch('requests.post', autospec=True)
    def test_send_signal_to_sigmax(self, mocked_request_post):
        mocked_request_post.return_value.status_code = 200
        mocked_request_post.return_value.text = 'Some text from Sigmax'

        call_command('send_signal_to_sigmax')

        args, kwargs = mocked_request_post.call_args
        self.assertIn('data', kwargs)
        self.assertEqual(kwargs['verify'], False)
        self.assertEqual(kwargs['url'], REQUIRED_ENV['SIGMAX_SERVER'])
        self.assertEqual(
            kwargs['headers']['Authorization'],
            'Basic ' + REQUIRED_ENV['SIGMAX_AUTH_TOKEN']
        )
