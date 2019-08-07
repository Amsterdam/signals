"""
Test suite for Sigmax message generation.
"""
import copy
import logging
from datetime import timedelta

from django.contrib.gis.geos import Point
from django.test import TestCase
from django.utils import timezone
from lxml import etree
from xmlunittest import XmlTestMixin

from signals.apps.sigmax.stuf_protocol.outgoing import _generate_sequence_number
from signals.apps.sigmax.stuf_protocol.outgoing.creeerZaak_Lk01 import (
    SIGMAX_REQUIRED_ADDRESS_FIELDS,
    SIGMAX_STADSDEEL_MAPPING,
    _address_matches_sigmax_expectation,
    _generate_creeerZaak_Lk01,
    _generate_omschrijving
)
from signals.apps.signals.models import Priority, Signal
from tests.apps.signals.factories import SignalFactory, SignalFactoryValidLocation
from tests.apps.signals.valid_locations import STADHUIS

logger = logging.getLogger(__name__)


class TestOutgoing(TestCase, XmlTestMixin):
    def test_generate_creeerZaak_Lk01(self):
        current_tz = timezone.get_current_timezone()
        location = Point(4.1234, 52.1234)
        signal = SignalFactory.create(incident_date_end=None, location__geometrie=location)

        seq_no = _generate_sequence_number(signal)
        xml_message = _generate_creeerZaak_Lk01(signal, seq_no)

        self.assertXmlDocument(xml_message)
        self.assertIn(
            f'<StUF:referentienummer>{signal.sia_id}.{seq_no}</StUF:referentienummer>',
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

        seq_no = _generate_sequence_number(signal)
        xml_message = _generate_creeerZaak_Lk01(signal, seq_no)

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

        seq_no = _generate_sequence_number(signal)
        xml_message = _generate_creeerZaak_Lk01(signal, seq_no)

        self.assertXmlDocument(xml_message)
        incident_date_end = signal.created_at + timedelta(days=3)
        self.assertIn(
            '<ZKN:einddatumGepland>{}</ZKN:einddatumGepland>'.format(
                incident_date_end.astimezone(current_tz).strftime('%Y%m%d')),
            xml_message)


class TestGenerateOmschrijving(TestCase):
    def setUp(self):
        self.signal = SignalFactoryValidLocation(priority__priority=Priority.PRIORITY_HIGH)

    def test_generate_omschrijving_urgent(self):
        stadsdeel = self.signal.location.stadsdeel

        correct = 'SIA-{}.02 URGENT {} {}'.format(
            self.signal.pk,
            SIGMAX_STADSDEEL_MAPPING.get(stadsdeel, 'SD--'),
            self.signal.location.short_address_text
        )

        seq_no = '02'
        self.assertEqual(_generate_omschrijving(self.signal, seq_no), correct)

    def test_generate_omschrijving_no_stadsdeel_urgent(self):
        # test that we get SD-- as part of the omschrijving when stadsdeel is missing
        self.signal.location.stadsdeel = None
        self.signal.location.save()

        correct = 'SIA-{}.04 URGENT SD-- {}'.format(
            self.signal.pk,
            self.signal.location.short_address_text
        )

        seq_no = '04'
        self.assertEqual(_generate_omschrijving(self.signal, seq_no), correct)


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


class TestGenerateCreeerZaakLk01Message(TestCase, XmlTestMixin):

    def setUp(self):
        self.signal: Signal = SignalFactoryValidLocation.create()
        self.seq_no = _generate_sequence_number(self.signal)

    def test_is_xml(self):
        msg = _generate_creeerZaak_Lk01(self.signal, self.seq_no)
        self.assertXmlDocument(msg)

    def test_escaping(self):
        poison: Signal = self.signal
        poison.text = '<poison>tastes nice</poison>'
        msg = _generate_creeerZaak_Lk01(poison, self.seq_no)
        self.assertTrue('<poison>' not in msg)

    def test_propagate_signal_properties_to_message_full_address(self):
        msg = _generate_creeerZaak_Lk01(self.signal, self.seq_no)
        current_tz = timezone.get_current_timezone()

        # first test that we have obtained valid XML
        root = etree.fromstring(msg)
        self.assertXmlDocument(msg)

        # Check whether our properties made it over
        # (crudely, maybe use XPATH here)
        need_to_find = dict([
            (
                '{http://www.egem.nl/StUF/StUF0301}referentienummer',
                f'{self.signal.sia_id}.{self.seq_no}'
            ),
            (
                '{http://www.egem.nl/StUF/sector/zkn/0310}identificatie',
                f'{self.signal.sia_id}.{self.seq_no}'
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

        msg = _generate_creeerZaak_Lk01(self.signal, self.seq_no)
        root = self.assertXmlDocument(msg)

        namespaces = {'zaak': 'http://www.egem.nl/StUF/sector/zkn/0310'}
        found = root.xpath('//zaak:object//zaak:heeftBetrekkingOp', namespaces=namespaces)
        self.assertEqual(found, [])
