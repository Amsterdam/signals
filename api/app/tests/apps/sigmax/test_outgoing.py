"""
Test suite for Sigmax message generation.
"""
import copy
import logging
import os
from datetime import timedelta
from unittest import mock

from django.contrib.gis.geos import Point
from django.test import TestCase, override_settings
from django.utils import timezone
from lxml import etree
from xmlunittest import XmlTestMixin

from signals.apps.sigmax import outgoing
from signals.apps.sigmax.models import CityControlRoundtrip
from signals.apps.sigmax.outgoing import (
    SIGMAX_REQUIRED_ADDRESS_FIELDS,
    SIGMAX_STADSDEEL_MAPPING,
    SigmaxException,
    _address_matches_sigmax_expectation,
    _generate_creeerZaak_Lk01,
    _generate_omschrijving,
    _generate_sequence_number,
    _generate_voegZaakdocumentToe_Lk01,
    handle
)
from signals.apps.signals.models import Priority, Signal
from tests.apps.signals.factories import SignalFactory, SignalFactoryValidLocation
from tests.apps.signals.valid_locations import STADHUIS

LOG_FORMAT = '%(asctime)-15s - %(name)s - %(message)s'
logging.basicConfig(format=LOG_FORMAT, level=logging.DEBUG)
logging.disable(logging.NOTSET)
logger = logging.getLogger(__name__)

REQUIRED_ENV = {'SIGMAX_AUTH_TOKEN': 'TEST', 'SIGMAX_SERVER': 'https://example.com'}
DATA_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'data'
)


class TestHandle(TestCase):
    def setUp(self):
        self.signal = SignalFactory.create()

    @mock.patch('signals.apps.sigmax.outgoing.MAX_ROUND_TRIPS', 2)
    @mock.patch('signals.apps.sigmax.outgoing.send_creeerZaak_Lk01', autospec=True)
    @mock.patch('signals.apps.sigmax.outgoing.send_voegZaakdocumentToe_Lk01', autospec=True)
    def test_too_many(self,
                      patched_send_voegZaakdocumentToe_Lk01,
                      patched_send_creeerZaak_Lk01,):
        CityControlRoundtrip.objects.create(_signal=self.signal)
        CityControlRoundtrip.objects.create(_signal=self.signal)
        CityControlRoundtrip.objects.create(_signal=self.signal)

        with self.assertRaises(SigmaxException):
            handle(self.signal)
        patched_send_voegZaakdocumentToe_Lk01.assert_not_called()

    @mock.patch('signals.apps.sigmax.outgoing.send_creeerZaak_Lk01', autospec=True)
    @mock.patch('signals.apps.sigmax.outgoing.send_voegZaakdocumentToe_Lk01', autospec=True)
    def test_success_message(self,
                             patched_send_voegZaakdocumentToe_Lk01,
                             patched_send_creeerZaak_Lk01):
        success_message = handle(self.signal)
        self.assertIn(
            '{}.01'.format(self.signal.sia_id),
            success_message
        )


class TestOutgoing(TestCase, XmlTestMixin):

    def test_generate_creeerZaak_Lk01(self):
        current_tz = timezone.get_current_timezone()
        location = Point(4.1234, 52.1234)
        signal = SignalFactory.create(incident_date_end=None, location__geometrie=location)

        xml_message = _generate_creeerZaak_Lk01(signal)
        sequence_number = _generate_sequence_number(signal)

        self.assertXmlDocument(xml_message)
        self.assertIn(
            f'<StUF:referentienummer>{signal.sia_id}.{sequence_number}</StUF:referentienummer>',
            xml_message)
        self.assertIn(
            '<StUF:tijdstipBericht>{}</StUF:tijdstipBericht>'.format(
                signal.created_at.astimezone(current_tz).strftime('%Y%m%d%H%M%S')),
            xml_message)
        self.assertIn(
            '<ZKN:startdatum>{}</ZKN:startdatum>'.format(
                signal.incident_date_start.astimezone(current_tz).strftime('%Y%m%d')),
            xml_message)
        incident_date_end = signal.created_at + timedelta(days=3)
        self.assertIn(
            '<ZKN:einddatumGepland>{}</ZKN:einddatumGepland>'.format(
                incident_date_end.astimezone(current_tz).strftime('%Y%m%d')),
            xml_message)
        self.assertIn(
            '<StUF:extraElement naam="Ycoordinaat">{}</StUF:extraElement>'.format(location.y),
            xml_message)
        self.assertIn(
            '<StUF:extraElement naam="Xcoordinaat">{}</StUF:extraElement>'.format(location.x),
            xml_message)

    def test_generate_creeerZaak_Lk01_priority_high(self):
        current_tz = timezone.get_current_timezone()
        signal = SignalFactory.create(incident_date_end=None,
                                      priority__priority=Priority.PRIORITY_HIGH)

        xml_message = _generate_creeerZaak_Lk01(signal)

        self.assertXmlDocument(xml_message)
        incident_date_end = signal.created_at + timedelta(days=1)
        self.assertIn(
            '<ZKN:einddatumGepland>{}</ZKN:einddatumGepland>'.format(
                incident_date_end.astimezone(current_tz).strftime('%Y%m%d')),
            xml_message)

    def test_generate_creeerZaak_Lk01_priority_normal(self):
        current_tz = timezone.get_current_timezone()
        signal = SignalFactory.create(incident_date_end=None,
                                      priority__priority=Priority.PRIORITY_NORMAL)

        xml_message = _generate_creeerZaak_Lk01(signal)

        self.assertXmlDocument(xml_message)
        incident_date_end = signal.created_at + timedelta(days=3)
        self.assertIn(
            '<ZKN:einddatumGepland>{}</ZKN:einddatumGepland>'.format(
                incident_date_end.astimezone(current_tz).strftime('%Y%m%d')),
            xml_message)

    def test_generate_voegZaakdocumentToe_Lk01(self):
        signal = SignalFactoryValidLocation.create()
        xml_message = _generate_voegZaakdocumentToe_Lk01(signal)
        sequence_number = _generate_sequence_number(signal)
        self.assertXmlDocument(xml_message)

        self.assertIn(
            f'<ZKN:identificatie>{signal.sia_id}.{sequence_number}</ZKN:identificatie>',
            xml_message
        )

    def test_generate_voegZaakdocumentToe_Lk01_escaping(self):
        poison = SignalFactoryValidLocation.create()
        poison.text = '<poison>tastes nice</poison>'
        xml_message = _generate_voegZaakdocumentToe_Lk01(poison)
        self.assertTrue('<poison>' not in xml_message)


class TestGenerateOmschrijving(TestCase):
    def setUp(self):
        self.signal = SignalFactoryValidLocation(priority__priority=Priority.PRIORITY_HIGH)

    @mock.patch(
        'signals.apps.sigmax.outgoing._generate_sequence_number', autospec=True, return_value='02')
    def test_generate_omschrijving_urgent(self, patched):
        stadsdeel = self.signal.location.stadsdeel

        correct = 'SIA-{}.02 URGENT {} {}'.format(
            self.signal.pk,
            SIGMAX_STADSDEEL_MAPPING.get(stadsdeel, 'SD--'),
            self.signal.location.short_address_text
        )

        self.assertEqual(_generate_omschrijving(self.signal), correct)
        patched.assert_called_once_with(self.signal)

    @mock.patch(
        'signals.apps.sigmax.outgoing._generate_sequence_number', autospec=True, return_value='04')
    def test_generate_omschrijving_no_stadsdeel_urgent(self, patched):
        # test that we get SD-- as part of the omschrijving when stadsdeel is missing
        self.signal.location.stadsdeel = None
        self.signal.location.save()

        correct = 'SIA-{}.04 URGENT SD-- {}'.format(
            self.signal.pk,
            self.signal.location.short_address_text
        )

        self.assertEqual(_generate_omschrijving(self.signal), correct)
        patched.assert_called_once_with(self.signal)


class TestAddressMatchesSigmaxExpectation(TestCase):
    def setUp(self):
        self.valid_address_dict = copy.copy(STADHUIS)  # has more fields than Location.address, so:
        self.valid_address_dict.pop('lon')
        self.valid_address_dict.pop('lat')
        self.valid_address_dict.pop('buurt_code')
        self.valid_address_dict.pop('stadsdeel')

    def test_full_valid(self):
        address_dict = copy.copy(self.valid_address_dict)

        self.assertEqual(True, _address_matches_sigmax_expectation(address_dict))

    def test_minimum_valid(self):
        address_dict = copy.copy(self.valid_address_dict)
        address_dict = {
            k: v for k, v in address_dict.items() if k in SIGMAX_REQUIRED_ADDRESS_FIELDS
        }

        self.assertEqual(True, _address_matches_sigmax_expectation(address_dict))

    def test_empty(self):
        self.assertEqual(False, _address_matches_sigmax_expectation({}))

    def test_invalid(self):
        address_dict = copy.copy(self.valid_address_dict)
        address_dict.pop('woonplaats')
        self.assertEqual(False, _address_matches_sigmax_expectation(address_dict))

        address_dict = copy.copy(self.valid_address_dict)
        address_dict.pop('openbare_ruimte')
        self.assertEqual(False, _address_matches_sigmax_expectation(address_dict))

        address_dict = copy.copy(self.valid_address_dict)
        address_dict.pop('huisnummer')
        self.assertEqual(False, _address_matches_sigmax_expectation(address_dict))

    def test_invalid_because_of_whitespace_values(self):
        address_dict = copy.copy(self.valid_address_dict)
        address_dict['woonplaats'] = ' '
        self.assertEqual(False, _address_matches_sigmax_expectation(address_dict))

        address_dict = copy.copy(self.valid_address_dict)
        address_dict['woonplaats'] = ' '
        self.assertEqual(False, _address_matches_sigmax_expectation(address_dict))

        address_dict = copy.copy(self.valid_address_dict)
        address_dict['woonplaats'] = ' '
        self.assertEqual(False, _address_matches_sigmax_expectation(address_dict))

    def test_none_value(self):
        # simulate empty address field
        self.assertEqual(False, _address_matches_sigmax_expectation(None))
        self.assertEqual(False, _address_matches_sigmax_expectation({}))


class TestGenerateSequenceNumber(TestCase):
    def setUp(self):
        self.signal = SignalFactory.create()

    def test_initial_sequence_number(self):
        self.assertEqual(CityControlRoundtrip.objects.count(), 0)
        self.assertEqual(_generate_sequence_number(self.signal), '01')

    def test_fourth_sequence_number(self):
        self.assertEqual(CityControlRoundtrip.objects.count(), 0)
        CityControlRoundtrip.objects.bulk_create([
            CityControlRoundtrip(_signal=self.signal),
            CityControlRoundtrip(_signal=self.signal),
            CityControlRoundtrip(_signal=self.signal),
        ])
        self.assertEqual(_generate_sequence_number(self.signal), '04')


class TestGenerateCreeerZaakLk01Message(TestCase, XmlTestMixin):

    def setUp(self):
        self.signal: Signal = SignalFactoryValidLocation.create()

    def test_is_xml(self):
        msg = outgoing._generate_creeerZaak_Lk01(self.signal)
        self.assertXmlDocument(msg)

    def test_escaping(self):
        poison: Signal = self.signal
        poison.text = '<poison>tastes nice</poison>'
        msg = outgoing._generate_creeerZaak_Lk01(poison)
        self.assertTrue('<poison>' not in msg)

    def test_propagate_signal_properties_to_message_full_address(self):
        msg = outgoing._generate_creeerZaak_Lk01(self.signal)
        current_tz = timezone.get_current_timezone()
        sequence_number = outgoing._generate_sequence_number(self.signal)

        # first test that we have obtained valid XML
        root = etree.fromstring(msg)
        self.assertXmlDocument(msg)

        # Check whether our properties made it over
        # (crudely, maybe use XPATH here)
        need_to_find = dict([
            (
                '{http://www.egem.nl/StUF/StUF0301}referentienummer',
                f'{self.signal.sia_id}.{sequence_number}'
            ),
            (
                '{http://www.egem.nl/StUF/sector/zkn/0310}identificatie',
                f'{self.signal.sia_id}.{sequence_number}'
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

        self.assertEqual(len(need_to_find), 0)

    def test_no_address_means_no_address_fields(self):
        self.signal.location.address = None
        self.signal.save()

        msg = outgoing._generate_creeerZaak_Lk01(self.signal)
        root = self.assertXmlDocument(msg)

        namespaces = {'zaak': 'http://www.egem.nl/StUF/sector/zkn/0310'}
        found = root.xpath('//zaak:object//zaak:heeftBetrekkingOp', namespaces=namespaces)
        self.assertEqual(found, [])


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

        self.assertEqual(outgoing._stuf_response_ok(fake_response), True)

    def test_Fo03(self):
        test_xml_file = os.path.join(DATA_DIR, 'example-fo03.xml')
        with open(test_xml_file, 'rt', encoding='utf-8') as f:
            test_xml = f.read()

        fake_response = mock.MagicMock()
        fake_response.text = test_xml

        self.assertEqual(outgoing._stuf_response_ok(fake_response), False)
