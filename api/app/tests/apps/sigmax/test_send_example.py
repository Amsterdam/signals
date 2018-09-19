import os
from unittest import mock

from django.core.management import call_command
from django.test import TestCase

REQUIRED_ENV = {'SIGMAX_AUTH_TOKEN': 'TEST', 'SIGMAX_SERVER': 'https://example.com'}

class CommandTestCase(TestCase):
    @mock.patch('requests.post', autospec=True)
    @mock.patch.dict(os.environ, REQUIRED_ENV)
    def test_send_signal_to_sigmax(self, mocked_request_post):
        mocked_request_post.return_value.status_code = 200
        mocked_request_post.return_value.text = 'ABACADABRA'

        call_command('send_example', '1')
        mocked_request_post.assert_called_once()

        args, kwargs = mocked_request_post.call_args
        self.assertEqual(kwargs['verify'], False)
        self.assertEqual(kwargs['url'], REQUIRED_ENV['SIGMAX_SERVER'])
        self.assertEqual(
            kwargs['headers']['Authorization'],
            'Basic ' + REQUIRED_ENV['SIGMAX_AUTH_TOKEN']
        )
