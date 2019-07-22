from unittest import mock

import lxml
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.test import TestCase
from lxml import etree

from signals.apps.sigmax.stuf_protocol.incoming import (
    ACTUALISEER_ZAAK_STATUS_SOAPACTION,
    _parse_actualiseerZaakstatus_Lk01,
    _parse_zaak_identificatie
)
from signals.apps.signals import workflow
from signals.apps.signals.models import Signal
from tests.apps.signals.factories import SignalFactoryValidLocation
from tests.test import SignalsBaseApiTestCase

REQUIRED_ENV = {'SIGMAX_AUTH_TOKEN': 'TEST', 'SIGMAX_SERVER': 'https://example.com'}
SOAP_ENDPOINT = '/signals/sigmax/soap'


class TestSoapEndpoint(SignalsBaseApiTestCase):
    def test_routing(self):
        """Check that routing for Sigmax is active and correct"""
        response = self.client.get(SOAP_ENDPOINT)
        self.assertNotEqual(response.status_code, 404)

    def test_http_verbs(self):
        """Check that the SOAP endpoint only accepts POST and OPTIONS"""
        not_allowed = ['GET', 'PUT', 'PATCH', 'DELETE', 'HEAD']
        allowed = ['POST', 'OPTIONS']

        self.client.force_authenticate(user=self.superuser)

        for verb in not_allowed:
            method = getattr(self.client, verb.lower())
            response = method(SOAP_ENDPOINT)
            self.assertEqual(
                response.status_code,
                405,
                f'{SOAP_ENDPOINT} must not accept HTTP method {verb}'
            )

        for verb in allowed:
            method = getattr(self.client, verb.lower())
            response = method(SOAP_ENDPOINT)
            self.assertNotEqual(
                response.status_code,
                405,
                f'{SOAP_ENDPOINT} must accept HTTP method {verb}'
            )

    def test_soap_action_missing(self):
        """SOAP endpoint must reject messages with missing SOAPaction header"""
        self.client.force_authenticate(user=self.superuser)

        response = self.client.post(SOAP_ENDPOINT)
        self.assertEqual(response.status_code, 500)
        self.assertIn('Fo03', response.content.decode('utf-8', 'strict'))

    @mock.patch('signals.apps.sigmax.views._handle_actualiseerZaakstatus_Lk01', autospec=True)
    @mock.patch('signals.apps.sigmax.views._handle_unknown_soap_action', autospec=True)
    def test_soap_action_routing(self, handle_unknown, handle_known):
        """Check that correct function is called based on SOAPAction header"""
        handle_unknown.return_value = HttpResponse('Required by view function')
        handle_known.return_value = HttpResponse('Required by view function')

        # authenticate
        self.client.force_authenticate(user=self.superuser)

        # check that actualiseerZaakstatus_lk01 is routed correctly
        self.client.post(SOAP_ENDPOINT, HTTP_SOAPACTION=ACTUALISEER_ZAAK_STATUS_SOAPACTION,
                         content_type='text/xml')
        handle_known.assert_called_once()
        handle_unknown.assert_not_called()
        handle_known.reset_mock()
        handle_unknown.reset_mock()

        # check that something else is send to _handle_unknown_soap_action
        wrong_action = 'http://example.com/unknown'
        self.client.post(SOAP_ENDPOINT, data='<a>DOES NOT MATTER</a>', HTTP_SOAPACTION=wrong_action,
                         content_type='text/xml')

        handle_known.assert_not_called()
        handle_unknown.assert_called_once()

    def test_wrong_soapaction_results_in_fo03(self):
        """Check that we send a StUF Fo03 when we receive an unknown SOAPAction"""
        # authenticate
        self.client.force_authenticate(user=self.superuser)

        # Check that wrong action is replied to with XML, StUF Fo03, status 500, utf-8 encoding.
        wrong_action = 'http://example.com/unknown'
        response = self.client.post(SOAP_ENDPOINT, data='<a>DOES NOT MATTER</a>',
                                    HTTP_SOAPACTION=wrong_action, content_type='text/xml')

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.charset, 'utf-8')
        xml_text = response.content.decode('utf-8')
        tree = etree.fromstring(xml_text)  # will fail if not XML

        namespaces = {'stuf': 'http://www.egem.nl/StUF/StUF0301'}
        found = tree.xpath('//stuf:stuurgegevens/stuf:berichtcode', namespaces=namespaces)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].text, 'Fo03')

    def test_no_signal_for_message(self):
        """Test that we generate a Fo03 if no signal can be found to go with it."""
        self.assertEqual(Signal.objects.count(), 0)

        mocked_signal = mock.Mock(sia_id='SIA-1234567890')
        # generate test message
        incoming_msg = render_to_string('sigmax/actualiseerZaakstatus_Lk01.xml', {
            'signal': mocked_signal,
            'tijdstipbericht': '20180927100000',
            'resultaat_omschrijving': 'HALLO',
        })

        # authenticate
        self.client.force_authenticate(user=self.superuser)

        # call our SOAP endpoint
        response = self.client.post(
            SOAP_ENDPOINT, data=incoming_msg, HTTP_SOAPACTION=ACTUALISEER_ZAAK_STATUS_SOAPACTION,
            content_type='text/xml',
        )

        # check that the request was rejected because no signal is present in database
        self.assertEqual(response.status_code, 500)
        self.assertIn('Melding met sia_id', response.content.decode('utf-8', 'strict'))

    def test_with_signal_for_message_wrong_state(self):
        signal = SignalFactoryValidLocation.create()
        self.assertEqual(Signal.objects.count(), 1)

        incoming_msg = render_to_string('sigmax/actualiseerZaakstatus_Lk01.xml', {
            'signal': signal,
            'tijdstipbericht': '20180927100000',
            'resultaat_omschrijving': 'HALLO',
        })

        # authenticate
        self.client.force_authenticate(user=self.superuser)

        # call our SOAP endpoint
        response = self.client.post(
            SOAP_ENDPOINT, data=incoming_msg, HTTP_SOAPACTION=ACTUALISEER_ZAAK_STATUS_SOAPACTION,
            content_type='text/xml',
        )

        self.assertEqual(response.status_code, 500)
        self.assertIn(str(signal.sia_id), response.content.decode('utf-8', 'strict'))
        self.assertIn('Fo03', response.content.decode('utf-8', 'strict'))

    def test_with_signal_for_message_correct_state(self):
        signal = SignalFactoryValidLocation.create()
        signal.status.state = workflow.VERZONDEN
        signal.status.save()
        signal.refresh_from_db()

        self.assertEqual(Signal.objects.count(), 1)

        incoming_context = {
            'signal': signal,
            'tijdstipbericht': '20180927100000',
            'resultaat_omschrijving': 'Op locatie geweest, niets aangetroffen',
            'resultaat_toelichting': 'Het probleem is opgelost',
            'resultaat_datum': '2018101111485276',
        }
        incoming_msg = render_to_string('sigmax/actualiseerZaakstatus_Lk01.xml', incoming_context)

        # authenticate
        self.client.force_authenticate(user=self.superuser)

        # call our SOAP endpoint
        response = self.client.post(
            SOAP_ENDPOINT,
            data=incoming_msg,
            HTTP_SOAPACTION=ACTUALISEER_ZAAK_STATUS_SOAPACTION,
            content_type='text/xml',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(str(signal.sia_id), response.content.decode('utf-8', 'strict'))
        self.assertIn('Bv03', response.content.decode('utf-8', 'strict'))

        signal.refresh_from_db()
        self.assertEqual(signal.status.state, workflow.AFGEHANDELD_EXTERN)
        self.assertEqual(
            signal.status.text,
            'Op locatie geweest, niets aangetroffen: Het probleem is opgelost'
        )
        self.assertEqual(signal.status.extra_properties, {
            'sigmax_datum_afgehandeld': incoming_context['resultaat_datum'],
            'sigmax_resultaat': incoming_context['resultaat_omschrijving'],
            'sigmax_reden': incoming_context['resultaat_toelichting'],
        })
        self.assertEqual(signal.status.state, workflow.AFGEHANDELD_EXTERN)
        self.assertEqual(signal.status.state, workflow.AFGEHANDELD_EXTERN)

    def test_with_signal_for_message_correct_state_new_style_zaak_identificatie(self):
        signal = SignalFactoryValidLocation.create()
        signal.status.state = workflow.VERZONDEN
        signal.status.save()
        signal.refresh_from_db()

        self.assertEqual(Signal.objects.count(), 1)

        incoming_context = {
            'signal': signal,
            'tijdstipbericht': '20180927100000',
            'resultaat_omschrijving': 'Op locatie geweest, niets aangetroffen',
            'resultaat_toelichting': 'Het probleem is opgelost',
            'resultaat_datum': '2018101111485276',
            'sequence_number': '05',
        }
        incoming_msg = render_to_string('sigmax/actualiseerZaakstatus_Lk01.xml', incoming_context)

        # authenticate
        self.client.force_authenticate(user=self.superuser)

        # call our SOAP endpoint
        response = self.client.post(
            SOAP_ENDPOINT,
            data=incoming_msg,
            HTTP_SOAPACTION=ACTUALISEER_ZAAK_STATUS_SOAPACTION,
            content_type='text/xml',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(str(signal.sia_id) + '.05', response.content.decode('utf-8', 'strict'))
        self.assertIn('Bv03', response.content.decode('utf-8', 'strict'))

        signal.refresh_from_db()
        self.assertEqual(signal.status.state, workflow.AFGEHANDELD_EXTERN)
        self.assertEqual(
            signal.status.text,
            'Op locatie geweest, niets aangetroffen: Het probleem is opgelost'
        )
        self.assertEqual(signal.status.extra_properties, {
            'sigmax_datum_afgehandeld': incoming_context['resultaat_datum'],
            'sigmax_resultaat': incoming_context['resultaat_omschrijving'],
            'sigmax_reden': incoming_context['resultaat_toelichting'],
        })
        self.assertEqual(signal.status.state, workflow.AFGEHANDELD_EXTERN)
        self.assertEqual(signal.status.state, workflow.AFGEHANDELD_EXTERN)

    def test_with_signal_for_message_correct_state_no_resultaat_toelichting(self):
        signal = SignalFactoryValidLocation.create()
        signal.status.state = workflow.VERZONDEN
        signal.status.save()
        signal.refresh_from_db()

        self.assertEqual(Signal.objects.count(), 1)

        incoming_context = {
            'signal': signal,
            'tijdstipbericht': '20180927100000',
            'resultaat_omschrijving': 'Op locatie geweest, niets aangetroffen',
            'resultaat_toelichting': '',  # is translated to 'reden' upon reception
            'resultaat_datum': '2018101111485276',
        }
        incoming_msg = render_to_string('sigmax/actualiseerZaakstatus_Lk01.xml', incoming_context)

        # authenticate
        self.client.force_authenticate(user=self.superuser)

        # call our SOAP endpoint
        response = self.client.post(
            SOAP_ENDPOINT,
            data=incoming_msg,
            HTTP_SOAPACTION=ACTUALISEER_ZAAK_STATUS_SOAPACTION,
            content_type='text/xml',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(str(signal.sia_id), response.content.decode('utf-8', 'strict'))
        self.assertIn('Bv03', response.content.decode('utf-8', 'strict'))

        signal.refresh_from_db()
        self.assertEqual(signal.status.state, workflow.AFGEHANDELD_EXTERN)
        self.assertEqual(
            signal.status.text,
            'Op locatie geweest, niets aangetroffen: Geen reden aangeleverd vanuit THOR'
        )
        self.assertEqual(signal.status.extra_properties, {
            'sigmax_datum_afgehandeld': incoming_context['resultaat_datum'],
            'sigmax_resultaat': incoming_context['resultaat_omschrijving'],
            'sigmax_reden': incoming_context['resultaat_toelichting'],
        })
        self.assertEqual(signal.status.state, workflow.AFGEHANDELD_EXTERN)
        self.assertEqual(signal.status.state, workflow.AFGEHANDELD_EXTERN)


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
