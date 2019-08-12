"""
Test suite for Sigmax message generation.
"""
import logging

from django.test import TestCase
from lxml import etree
from xmlunittest import XmlTestMixin

from signals.apps.sigmax.stuf_protocol.outgoing import _generate_sequence_number
from signals.apps.sigmax.stuf_protocol.outgoing.voegZaakdocumentToe_Lk01 import (
    _generate_voegZaakdocumentToe_Lk01
)
from signals.apps.signals.models import Signal
from tests.apps.signals.factories import SignalFactoryValidLocation

logger = logging.getLogger(__name__)


class TestGenerateVoegZaakDocumentToe_LK01(TestCase, XmlTestMixin):
    def test_generate_voegZaakdocumentToe_Lk01(self):
        signal = SignalFactoryValidLocation.create()
        seq_no = _generate_sequence_number(signal)
        xml_message = _generate_voegZaakdocumentToe_Lk01(signal, seq_no)
        self.assertXmlDocument(xml_message)

        self.assertIn(
            f'<ZKN:identificatie>{signal.sia_id}.{seq_no}</ZKN:identificatie>',
            xml_message
        )

    def test_generate_voegZaakdocumentToe_Lk01_escaping(self):
        poison = SignalFactoryValidLocation.create()
        poison.text = '<poison>tastes nice</poison>'
        seq_no = '02'
        xml_message = _generate_voegZaakdocumentToe_Lk01(poison, seq_no)
        self.assertTrue('<poison>' not in xml_message)


class TestVoegZaakDocumentToeLk01Message(TestCase):

    def setUp(self):
        self.signal: Signal = SignalFactoryValidLocation.create()
        self.seq_no = _generate_sequence_number(self.signal)

    def test_is_xml(self):
        signal = self.signal
        xml = _generate_voegZaakdocumentToe_Lk01(signal, self.seq_no)
        try:
            etree.fromstring(xml)
        except Exception:
            self.fail('Cannot parse STUF message as XML')

    def test_escaping(self):
        poison: Signal = self.signal
        poison.text = '<poison>tastes nice</poison>'
        xml = _generate_voegZaakdocumentToe_Lk01(poison, self.seq_no)
        self.assertTrue('<poison>' not in xml)
