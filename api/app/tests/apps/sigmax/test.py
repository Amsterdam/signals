"""
Test suite for Sigmax message generation.
"""
import datetime
import logging
import time
from unittest import mock

from django.test import TestCase, override_settings
from lxml import etree

from signals.apps.sigmax import handler, utils
from signals.apps.signals.models import Signal
from tests.apps.signals.factories import SignalFactory

LOG_FORMAT = '%(asctime)-15s - %(name)s - %(message)s'
logging.basicConfig(format=LOG_FORMAT, level=logging.DEBUG)
logging.disable(logging.NOTSET)
logger = logging.getLogger(__name__)


class TestSigmaxHelpers(TestCase):
    def test_format_datetime(self):
        dt = datetime.datetime(2018, 7, 9, 10, 0, 30)
        self.assertEqual(
            utils._format_datetime(dt),
            '20180709100030'
        )

        dt = datetime.datetime(2018, 7, 9, 22, 0, 30)
        self.assertEqual(
            utils._format_datetime(dt),
            '20180709220030'
        )

    def test_format_date(self):
        dt = datetime.datetime(2018, 7, 9, 10, 59, 34)
        self.assertEqual(
            utils._format_date(dt),
            '20180709'
        )

    def test_wrong_type(self):
        with self.assertRaises(AttributeError):
            utils._format_datetime(None)
        with self.assertRaises(AttributeError):
            t = time.time()
            utils._format_datetime(t)

        with self.assertRaises(AttributeError):
            utils._format_date(None)
        with self.assertRaises(AttributeError):
            t = time.time()
            utils._format_date(t)


class TestGenerateCreeerZaakLk01Message(TestCase):

    def setUp(self):
        self.signal: Signal = SignalFactory.create()

    def test_is_xml(self):
        xml = handler._generate_creeer_zaak_lk01_message(self.signal)

        try:
            etree.fromstring(xml)
        except Exception:
            self.fail('Cannot parse STUF message as XML')

    def test_escaping(self):
        poison: Signal = self.signal
        poison.text = '<poison>tastes nice</poison>'
        msg = handler._generate_creeer_zaak_lk01_message(poison)
        self.assertTrue('<poison>' not in msg)

    def test_propagate_signal_properties_to_message(self):
        msg = handler._generate_creeer_zaak_lk01_message(self.signal)

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
                utils._format_datetime(self.signal.created_at)
            ),
            (
                '{http://www.egem.nl/StUF/sector/zkn/0310}registratiedatum',
                utils._format_date(self.signal.created_at)
            ),
            (
                '{http://www.egem.nl/StUF/sector/zkn/0310}startdatum',
                utils._format_date(self.signal.incident_date_start)
            ),
            (
                '{http://www.egem.nl/StUF/sector/zkn/0310}einddatumGepland',
                utils._format_date(self.signal.incident_date_end)
            )
        ])
        # X and Y need to be checked differently

        logger.debug(msg)

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
        self.signal: Signal = SignalFactory.create()

    def test_is_xml(self):
        signal = self.signal
        xml = handler._generate_voeg_zaak_document_toe_lk01(signal)
        try:
            etree.fromstring(xml)
        except Exception:
            self.fail('Cannot parse STUF message as XML')

    def test_escaping(self):
        poison: Signal = self.signal
        poison.text = '<poison>tastes nice</poison>'
        msg = handler._generate_voeg_zaak_document_toe_lk01(poison)
        self.assertTrue('<poison>' not in msg)


def show_args_kwargs(*args, **kwargs):
    return args, kwargs


class TestSendStufMessage(TestCase):
    def test_no_environment_variables(self):
        # Check that missing enviroment variables for server and auth token
        # raises an error when a message is sent.
        env_override = {'SIGMAX_AUTH_TOKEN': '', 'SIGMAX_SERVER': ''}

        with mock.patch.dict('os.environ', env_override):
            with self.assertRaises(handler.ServiceNotConfigured):
                action = 'http://www.egem.nl/StUF/sector/zkn/0310/CreeerZaak_Lk01'
                handler._send_stuf_message('TEST BERICHT', action)

    @mock.patch('requests.post', side_effect=show_args_kwargs)
    @override_settings(SIGMAX_AUTH_TOKEN='SLEUTEL')
    @override_settings(SIGMAX_SERVER='TESTSERVER')
    def test_send_message(self, request_post_mock):
        # Check that headers are set correctly when sending an STUF message.
        message = 'TEST BERICHT'
        action = 'http://www.egem.nl/StUF/sector/zkn/0310/CreeerZaak_Lk01'
        args, kwargs = handler._send_stuf_message(message, action)

        self.assertEquals(request_post_mock.called, 1)
        self.assertEquals(kwargs['url'], 'TESTSERVER')
        self.assertEquals(
            kwargs['headers']['Authorization'],
            'Basic SLEUTEL'
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
