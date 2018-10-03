from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from xmlunittest import XmlTestMixin

from signals.apps.sigmax.outgoing import _generate_creeerZaak_Lk01
from signals.apps.signals.models import Priority
from tests.apps.signals.factories import SignalFactory


class TestOutgoing(TestCase, XmlTestMixin):

    def test_generate_creeerZaak_Lk01(self):
        current_tz = timezone.get_current_timezone()
        signal = SignalFactory.create(incident_date_end=None)

        xml_message = _generate_creeerZaak_Lk01(signal)

        self.assertXmlDocument(xml_message)
        self.assertIn(
            '<StUF:referentienummer>{}</StUF:referentienummer>'.format(signal.signal_id),
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
