"""
Test suite for Sigmax message generation.
"""
import logging
import os
from unittest import mock

from django.test import TestCase, override_settings

from signals.apps.sigmax.stuf_protocol import outgoing
from signals.apps.sigmax.stuf_protocol.exceptions import SigmaxException

logger = logging.getLogger(__name__)

REQUIRED_ENV = {'SIGMAX_AUTH_TOKEN': 'TEST', 'SIGMAX_SERVER': 'https://example.com'}
DATA_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'data'
)


class TestSendStufMessage(TestCase):
    @override_settings(
        SIGMAX_AUTH_TOKEN='',
        SIGMAX_SERVER='',
    )
    def test_no_environment_variables(self):
        # Check that missing enviroment variables for server and auth token
        # raises an error when a message is sent.
        env_override = {'SIGMAX_AUTH_TOKEN': '', 'SIGMAX_SERVER': ''}

        with mock.patch.dict('os.environ', env_override):
            with self.assertRaises(SigmaxException):
                action = 'http://www.egem.nl/StUF/sector/zkn/0310/CreeerZaak_Lk01'
                outgoing.stuf._send_stuf_message('TEST BERICHT', action)

    @override_settings(
        SIGMAX_AUTH_TOKEN=REQUIRED_ENV['SIGMAX_AUTH_TOKEN'],
        SIGMAX_SERVER=REQUIRED_ENV['SIGMAX_SERVER'],
    )
    @mock.patch('signals.apps.sigmax.stuf_protocol.outgoing.stuf._stuf_response_ok', autospec=True)
    @mock.patch('requests.post', autospec=True)
    def test_send_message(self, mocked_request_post, mocked_stuf_response_ok):
        mocked_request_post.return_value.status_code = 200
        mocked_request_post.return_value.text = 'Message from Sigmax'
        mocked_stuf_response_ok.return_value = True

        message = 'TEST BERICHT'
        action = 'http://www.egem.nl/StUF/sector/zkn/0310/CreeerZaak_Lk01'
        outgoing.stuf._send_stuf_message(message, action)

        # Check that headers are set correctly when sending an STUF message.
        args, kwargs = mocked_request_post.call_args

        self.assertEqual(mocked_request_post.called, 1)
        self.assertEqual(kwargs['url'], REQUIRED_ENV['SIGMAX_SERVER'])
        self.assertEqual(
            kwargs['headers']['Authorization'],
            'Basic ' + REQUIRED_ENV['SIGMAX_AUTH_TOKEN']
        )
        self.assertEqual(
            kwargs['headers']['SOAPAction'],
            'http://www.egem.nl/StUF/sector/zkn/0310/CreeerZaak_Lk01'
        )
        self.assertEqual(
            kwargs['headers']['Content-Type'],
            'text/xml; charset=UTF-8'
        )
        self.assertEqual(
            b'%d' % len(message),
            kwargs['headers']['Content-Length']
        )


class TestStufResponseOk(TestCase):
    def test_Bv03(self):
        test_xml_file = os.path.join(DATA_DIR, 'example-bv03.xml')
        with open(test_xml_file, 'rt', encoding='utf-8') as f:
            test_xml = f.read()

        fake_response = mock.MagicMock()
        fake_response.text = test_xml

        self.assertEqual(outgoing.stuf._stuf_response_ok(fake_response), True)

    def test_Fo03(self):
        test_xml_file = os.path.join(DATA_DIR, 'example-fo03.xml')
        with open(test_xml_file, 'rt', encoding='utf-8') as f:
            test_xml = f.read()

        fake_response = mock.MagicMock()
        fake_response.text = test_xml

        self.assertEqual(outgoing.stuf._stuf_response_ok(fake_response), False)
