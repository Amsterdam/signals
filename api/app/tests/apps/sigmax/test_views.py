"""
Test reception of StUF SOAP requests.
"""

from unittest import mock

from django.http import HttpResponse
from django.template.loader import render_to_string
from lxml import etree

from signals.apps.sigmax.stuf_protocol.incoming.actualiseerZaakstatus_Lk01 import (
    ACTUALISEER_ZAAK_STATUS
)
from signals.apps.signals import workflow
from signals.apps.signals.models import History, Signal
from tests.apps.signals.factories import SignalFactoryValidLocation
from tests.test import SignalsBaseApiTestCase

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

    @mock.patch('signals.apps.sigmax.views.handle_actualiseerZaakstatus_Lk01', autospec=True)
    @mock.patch('signals.apps.sigmax.views.handle_unsupported_soap_action', autospec=True)
    def test_soap_action_routing(self, handle_unsupported, handle_known):
        """Check that correct function is called based on SOAPAction header"""
        handle_unsupported.return_value = HttpResponse('Required by view function')
        handle_known.return_value = HttpResponse('Required by view function')

        # authenticate
        self.client.force_authenticate(user=self.superuser)

        # check that actualiseerZaakstatus_lk01 is routed correctly
        self.client.post(SOAP_ENDPOINT, HTTP_SOAPACTION=ACTUALISEER_ZAAK_STATUS,
                         content_type='text/xml')
        handle_known.assert_called_once()
        handle_unsupported.assert_not_called()
        handle_known.reset_mock()
        handle_unsupported.reset_mock()

        # check that something else is send to handle_unsupported_soap_action
        wrong_action = 'http://example.com/unsupported'
        self.client.post(SOAP_ENDPOINT, data='<a>DOES NOT MATTER</a>', HTTP_SOAPACTION=wrong_action,
                         content_type='text/xml')

        handle_known.assert_not_called()
        handle_unsupported.assert_called_once()

    def test_wrong_soapaction_results_in_fo03(self):
        """Check that we send a StUF Fo03 when we receive an unsupported SOAPAction"""
        # authenticate
        self.client.force_authenticate(user=self.superuser)

        # Check that wrong action is replied to with XML, StUF Fo03, status 500, utf-8 encoding.
        wrong_action = 'http://example.com/unsupported'
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
            SOAP_ENDPOINT, data=incoming_msg, HTTP_SOAPACTION=ACTUALISEER_ZAAK_STATUS,
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
            SOAP_ENDPOINT, data=incoming_msg, HTTP_SOAPACTION=ACTUALISEER_ZAAK_STATUS,
            content_type='text/xml',
        )

        self.assertEqual(response.status_code, 500)
        self.assertIn(str(signal.sia_id), response.content.decode('utf-8', 'strict'))
        self.assertIn('Fo03', response.content.decode('utf-8', 'strict'))

        last_update = History.objects.filter(_signal__id=signal.pk).order_by('-when').first()
        self.assertEqual(last_update.what, 'CREATE_NOTE')
        self.assertTrue(last_update.description.startswith(
            'Zaak status update ontvangen van CityControl terwijl SIA melding niet in verzonden staat was.'))  # noqa

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
            HTTP_SOAPACTION=ACTUALISEER_ZAAK_STATUS,
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
            HTTP_SOAPACTION=ACTUALISEER_ZAAK_STATUS,
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
            HTTP_SOAPACTION=ACTUALISEER_ZAAK_STATUS,
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
