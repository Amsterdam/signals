"""
Test suite for Sigmax message generation.
"""
import logging
import os
from unittest import mock

from django.test import TestCase, override_settings
from django.utils import timezone
from lxml import etree

from signals.apps.sigmax import outgoing
from signals.apps.signals.models import Signal
from tests.apps.signals.factories import SignalFactoryValidLocation

LOG_FORMAT = '%(asctime)-15s - %(name)s - %(message)s'
logging.basicConfig(format=LOG_FORMAT, level=logging.DEBUG)
logging.disable(logging.NOTSET)
logger = logging.getLogger(__name__)

REQUIRED_ENV = {'SIGMAX_AUTH_TOKEN': 'TEST', 'SIGMAX_SERVER': 'https://example.com'}
DATA_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'data'
)


class TestGenerateCreeerZaakLk01Message(TestCase):

    def setUp(self):
        self.signal: Signal = SignalFactoryValidLocation.create()

    def test_is_xml(self):
        msg = outgoing._generate_creeerZaak_Lk01(self.signal)
        try:
            etree.fromstring(msg)
        except Exception:
            self.fail('Cannot parse STUF message as XML')

    def test_escaping(self):
        poison: Signal = self.signal
        poison.text = '<poison>tastes nice</poison>'
        msg = outgoing._generate_creeerZaak_Lk01(poison)
        self.assertTrue('<poison>' not in msg)

    def test_propagate_signal_properties_to_message(self):
        msg = outgoing._generate_creeerZaak_Lk01(self.signal)
        current_tz = timezone.get_current_timezone()

        # first test that we have obtained valid XML
        try:
            root = etree.fromstring(msg)
        except Exception:
            self.fail('Cannot parse STUF message as XML')

        # Check whether our properties made it over
        # (crudely, maybe use XPATH here)
        need_to_find = dict([
            (
                '{http://www.egem.nl/StUF/StUF0301}referentienummer',
                self.signal.signal_id
            ),
            (
                '{http://www.egem.nl/StUF/sector/zkn/0310}identificatie',
                self.signal.signal_id
            ),
            (
                '{http://www.egem.nl/StUF/sector/bg/0310}gor.openbareRuimteNaam',
                self.signal.location.address['openbare_ruimte']
            ),
            (
                '{http://www.egem.nl/StUF/sector/bg/0310}huisnummer',
                self.signal.location.address['huisnummer']
            ),
            (
                '{http://www.egem.nl/StUF/sector/bg/0310}postcode',
                self.signal.location.address['postcode']
            ),
            (
                '{http://www.egem.nl/StUF/StUF0301}tijdstipBericht',
                self.signal.created_at.astimezone(current_tz).strftime('%Y%m%d%H%M%S')
            ),
            (
                '{http://www.egem.nl/StUF/sector/zkn/0310}registratiedatum',
                self.signal.created_at.astimezone(current_tz).strftime('%Y%m%d')
            ),
            (
                '{http://www.egem.nl/StUF/sector/zkn/0310}startdatum',
                self.signal.incident_date_start.astimezone(current_tz).strftime('%Y%m%d')
            ),
            (
                '{http://www.egem.nl/StUF/sector/zkn/0310}einddatumGepland',
                self.signal.incident_date_end.astimezone(current_tz).strftime('%Y%m%d')
            )
        ])
        # X and Y need to be checked differently
        for element in root.iter():
            # logger.debug('Found: {}'.format(element.tag))
            if element.tag in need_to_find:
                correct = str(need_to_find[element.tag]) == element.text
                if correct:
                    del need_to_find[element.tag]
                else:
                    logger.debug('Found {} and is correct {}'.format(
                        element.tag, correct))
                    logger.debug('element.text {}'.format(element.text))

        self.assertEquals(len(need_to_find), 0)


class TestVoegZaakDocumentToeLk01Message(TestCase):

    def setUp(self):
        self.signal: Signal = SignalFactoryValidLocation.create()

    def test_is_xml(self):
        signal = self.signal
        xml = outgoing._generate_voegZaakdocumentToe_Lk01(signal)
        try:
            etree.fromstring(xml)
        except Exception:
            self.fail('Cannot parse STUF message as XML')

    def test_escaping(self):
        poison: Signal = self.signal
        poison.text = '<poison>tastes nice</poison>'
        xml = outgoing._generate_voegZaakdocumentToe_Lk01(poison)
        self.assertTrue('<poison>' not in xml)


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
            with self.assertRaises(outgoing.SigmaxException):
                action = 'http://www.egem.nl/StUF/sector/zkn/0310/CreeerZaak_Lk01'
                outgoing._send_stuf_message('TEST BERICHT', action)

    @override_settings(
        SIGMAX_AUTH_TOKEN=REQUIRED_ENV['SIGMAX_AUTH_TOKEN'],
        SIGMAX_SERVER=REQUIRED_ENV['SIGMAX_SERVER'],
    )
    @mock.patch('signals.apps.sigmax.outgoing._stuf_response_ok', autospec=True)
    @mock.patch('requests.post', autospec=True)
    def test_send_message(self, mocked_request_post, mocked_stuf_response_ok):
        mocked_request_post.return_value.status_code = 200
        mocked_request_post.return_value.text = 'Message from Sigmax'
        mocked_stuf_response_ok.return_value = True

        message = 'TEST BERICHT'
        action = 'http://www.egem.nl/StUF/sector/zkn/0310/CreeerZaak_Lk01'
        outgoing._send_stuf_message(message, action)

        # Check that headers are set correctly when sending an STUF message.
        args, kwargs = mocked_request_post.call_args

        self.assertEquals(mocked_request_post.called, 1)
        self.assertEquals(kwargs['url'], REQUIRED_ENV['SIGMAX_SERVER'])
        self.assertEquals(
            kwargs['headers']['Authorization'],
            'Basic ' + REQUIRED_ENV['SIGMAX_AUTH_TOKEN']
        )
        self.assertEquals(
            kwargs['headers']['SOAPAction'],
            'http://www.egem.nl/StUF/sector/zkn/0310/CreeerZaak_Lk01'
        )
        self.assertEquals(
            kwargs['headers']['Content-Type'],
            'text/xml; charset=UTF-8'
        )
        self.assertEquals(
            bytes(len(message)),
            kwargs['headers']['Content-Length']
        )


class TestStufResponseOk(TestCase):
    def test_Bv03(self):
        test_xml_file = os.path.join(DATA_DIR, 'example-bv03.xml')
        with open(test_xml_file, 'rt', encoding='utf-8') as f:
            test_xml = f.read()

        fake_response = mock.MagicMock()
        fake_response.text = test_xml

        self.assertEqual(outgoing._stuf_response_ok(fake_response), True)

    def test_Fo03(self):
        test_xml_file = os.path.join(DATA_DIR, 'example-fo03.xml')
        with open(test_xml_file, 'rt', encoding='utf-8') as f:
            test_xml = f.read()

        fake_response = mock.MagicMock()
        fake_response.text = test_xml

        self.assertEqual(outgoing._stuf_response_ok(fake_response), False)
