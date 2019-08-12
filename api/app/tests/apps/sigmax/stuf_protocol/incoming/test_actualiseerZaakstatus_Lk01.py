"""
Test support for actualiseerZaakstatus_Lk01 StUF messages from CityControl/Sigmax.

See also: api/app/tests/apps/sigmax/test_views.py (relative to repository root)
"""
import lxml
from django.template.loader import render_to_string
from django.test import TestCase

from signals.apps.sigmax.stuf_protocol.incoming.actualiseerZaakstatus_Lk01 import (
    _parse_actualiseerZaakstatus_Lk01,
    _parse_zaak_identificatie
)
from tests.apps.signals.factories import SignalFactoryValidLocation


class TestProcessTestActualiseerZaakStatus(TestCase):
    def test_reject_not_xml(self):
        test_msg = b'THIS IS NOT XML'
        with self.assertRaises(lxml.etree.XMLSyntaxError):
            _parse_actualiseerZaakstatus_Lk01(test_msg)

    def test_extract_properties(self):
        signal = SignalFactoryValidLocation()

        test_context = {
            'signal': signal,
            'resultaat_toelichting': 'Het probleem is opgelost',
            'resultaat_datum': '2018101111485276',
            'sequence_number': 20,
        }
        test_msg = render_to_string('sigmax/actualiseerZaakstatus_Lk01.xml', test_context)
        msg_content = _parse_actualiseerZaakstatus_Lk01(test_msg.encode('utf8'))

        # test uses knowledge of test XML message content
        self.assertEqual(msg_content['zaak_id'], str(signal.sia_id) + '.20')  # TODO clean-up
        self.assertEqual(msg_content['datum_afgehandeld'], test_context['resultaat_datum'])
        self.assertEqual(msg_content['resultaat'], 'Er is gehandhaafd')
        self.assertEqual(msg_content['reden'], test_context['resultaat_toelichting'])


class TestParseZaakIdentificatie(TestCase):
    def test_correct_zaak_identificatie(self):
        # Test backwards compatibility
        self.assertEqual(_parse_zaak_identificatie('SIA-111'), (111, None))

        # Test new style
        self.assertEqual(_parse_zaak_identificatie('SIA-123.01'), (123, 1))
        self.assertEqual(_parse_zaak_identificatie('SIA-99.05'), (99, 5))

        # Accept extra white space before and/or after SIA id and sequence number
        self.assertEqual(_parse_zaak_identificatie('SIA-99.05  '), (99, 5))
        self.assertEqual(_parse_zaak_identificatie('  SIA-99.05  '), (99, 5))
        self.assertEqual(_parse_zaak_identificatie('  SIA-99.05'), (99, 5))

    def test_wrong_zaak_identificatie(self):
        should_fail = [
            # Do not accept 0 padding in SIA id
            'SIA-0',
            'SIA-0.01',
            'SIA-01',
            'SIA-01.01',

            # Do not accept 0 as a sequence number
            'SIA-1.00',

            # Too high sequence number (max two digits)
            'SIA-1.100',

            # SIA id must be present
            'SIA-.01',

            # Do not accept whitespace inside the SIA id and sequence number
            'SIA- 123',
            'SIA- 123.01',
            'SIA-123. 01',
            'SIA-123 .01',

            # Miscellaneous misspellings
            'SII-111',
            'SIA-99.05.02',
            'SIA-99.05 .02',
            'SIA-99.O5',
        ]
        for wrong_zaak_identificatie in should_fail:
            with self.assertRaises(ValueError):
                _parse_zaak_identificatie(wrong_zaak_identificatie)

    def test_empty_zaak_identificatie(self):
        with self.assertRaises(ValueError):
            _parse_zaak_identificatie('')

        with self.assertRaises(ValueError):
            _parse_zaak_identificatie('SIA-')

    def test_incorrect_type(self):
        with self.assertRaises(ValueError):
            _parse_zaak_identificatie(None)
