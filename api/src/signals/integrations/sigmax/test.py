"""
Test suite for Sigmax message generation.
"""
import copy
import datetime
import json
import logging
import os
import time
from unittest import mock
from xml import etree

from dateutil.parser import parse
from django.conf import settings
from django.test import TestCase

import utils
from signals.integrations.sigmax import utils, handler

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
    @classmethod
    def setUpClass(cls):
        fixture_file = os.path.join(
            settings.FIXTURES_DIR, 'datasets', 'internal', 'auth_signal.json')

        with open(fixture_file, 'r') as f:
            test_data = json.load(f)
        cls._example_signal = test_data['results'][0]

    @classmethod
    def tearDownClass(cls):
        pass

    def test_is_xml(self):
        signal = copy.deepcopy(self._example_signal)
        xml = handler._generate_creeer_zaak_lk01_message(signal)

        try:
            root = etree.fromstring(xml)
        except:
            self.fail('Cannot parse STUF message as XML')

    def test_escaping(self):
        poison = copy.deepcopy(self._example_signal)
        poison.update({'signal_id': '<poison>tastes nice</poison>'})
        msg = handler._generate_creeer_zaak_lk01_message(poison)
        self.assertTrue('<poison>' not in msg)

    def test_propagate_signal_properties_to_message(self):
        signal = copy.deepcopy(self._example_signal)

        msg = handler._generate_creeer_zaak_lk01_message(signal)

        # first test that we have obtained valid XML
        try:
            root = etree.fromstring(msg)
        except:
            self.fail('Cannot parse STUF message as XML')

        # Check whether our properties made it over (crudely, maybe use XPATH here)
        NEED_TO_FIND = dict([
            (
                '{http://www.egem.nl/StUF/StUF0301}referentienummer',
                signal['signal_id']
            ),
            (
                '{http://www.egem.nl/StUF/sector/zkn/0310}identificatie',
                signal['signal_id']
            ),
            (
                '{http://www.egem.nl/StUF/sector/bg/0310}gor.openbareRuimteNaam',
                signal['location']['address']['openbare_ruimte']
            ),
            (
                '{http://www.egem.nl/StUF/sector/bg/0310}huisnummer',
                signal['location']['address']['huisnummer']
            ),
            (
                '{http://www.egem.nl/StUF/sector/bg/0310}postcode',
                signal['location']['address']['postcode']
            ),
            (
                '{http://www.egem.nl/StUF/StUF0301}tijdstipBericht',
                utils._format_datetime(parse(signal['created_at']))
            ),
            (
                '{http://www.egem.nl/StUF/sector/zkn/0310}registratiedatum',
                utils._format_date(parse(signal['created_at']))
            ),
            (
                '{http://www.egem.nl/StUF/sector/zkn/0310}startdatum',
                utils._format_date(parse(signal['incident_date_start']))
            ),
            (
                '{http://www.egem.nl/StUF/sector/zkn/0310}einddatumGepland',
                utils._format_date(parse(signal['incident_date_end']))
            )
        ])
        # X and Y need to be checked differently

        logger.debug(msg)

        for element in root.iter():
            # logger.debug('Found: {}'.format(element.tag))
            if element.tag in NEED_TO_FIND:
                correct = NEED_TO_FIND[element.tag] == element.text
                if correct:
                    del NEED_TO_FIND[element.tag]
                else:
                    logger.debug('Found {} and is correct {}'.format(
                        element.tag, correct))
                    logger.debug('element.text {}'.format(element.text))

        self.assertEquals(len(NEED_TO_FIND), 0)


class TestVoegZaakDocumentToeLk01Message(TestCase):
    @classmethod
    def setUpClass(cls):
        fixture_file = os.path.join(
            settings.FIXTURES_DIR, 'datasets', 'internal', 'auth_signal.json')

        with open(fixture_file, 'r') as f:
            test_data = json.load(f)
        cls._example_signal = test_data['results'][0]

    @classmethod
    def tearDownClass(cls):
        pass

    def test_is_xml(self):
        signal = copy.deepcopy(self._example_signal)
        xml = handler._generate_voeg_zaak_document_toe_lk01(signal)
        try:
            root = etree.fromstring(xml)
        except:
            self.fail('Cannot parse STUF message as XML')

    def test_escaping(self):
        poison = copy.deepcopy(self._example_signal)
        poison.update({'signal_id': '<poison>tastes nice</poison>'})
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
    def test_send_message(self, request_post_mock):
        # Check that headers are set correctly when sending an STUF message.
        message = 'TEST BERICHT'
        env_override = {
            'SIGMAX_AUTH_TOKEN': 'SLEUTEL',
            'SIGMAX_SERVER': 'TESTSERVER',
        }

        with mock.patch.dict('os.environ', env_override):
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
