import uuid
from unittest import mock

import lxml
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.test import TestCase
from rest_framework.test import APITestCase

from signals.apps.sigmax.views import (
    ACTUALISEER_ZAAK_STATUS_SOAPACTION,
    _parse_actualiseerZaakstatus_Lk01
)
from signals.apps.signals import workflow
from signals.apps.signals.models import Signal
from tests.apps.signals.factories import SignalFactoryValidLocation
from tests.apps.users.factories import SuperUserFactory

REQUIRED_ENV = {'SIGMAX_AUTH_TOKEN': 'TEST', 'SIGMAX_SERVER': 'https://example.com'}
SOAP_ENDPOINT = '/signals/sigmax/soap'


class TestSoapEndpoint(APITestCase):
    def test_routing(self):
        """Check that routing for Sigmax is active and correct"""
        response = self.client.get(SOAP_ENDPOINT)
        self.assertNotEqual(response.status_code, 404)

    def test_http_verbs(self):
        """Check that the SOAP endpoint only accepts POST and OPTIONS"""
        not_allowed = ['GET', 'PUT', 'PATCH', 'DELETE', 'HEAD']
        allowed = ['POST', 'OPTIONS']

        superuser = SuperUserFactory.create()
        self.client.force_authenticate(user=superuser)

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
        superuser = SuperUserFactory.create()
        self.client.force_authenticate(user=superuser)

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
        superuser = SuperUserFactory.create()
        self.client.force_authenticate(user=superuser)

        # check that actualiseerZaakstatus_lk01 is routed correctly
        self.client.post(SOAP_ENDPOINT, SOAPAction=ACTUALISEER_ZAAK_STATUS_SOAPACTION,
                         content_type='text/xml')
        handle_known.assert_called_once()
        handle_unknown.assert_not_called()
        handle_known.reset_mock()
        handle_unknown.reset_mock()

        # check that something else is send to _handle_unknown_soap_action
        wrong_action = 'http://example.com/unknown'
        self.client.post(SOAP_ENDPOINT, data='<a>DOES NOT MATTER</a>', SOAPAction=wrong_action,
                         content_type='text/xml')

        handle_known.assert_not_called()
        handle_unknown.assert_called_once()

    def test_no_signal_for_message(self):
        """Test that we generate a Fo03 if no signal can be found to go with it."""
        self.assertEqual(Signal.objects.count(), 0)

        # generate test message
        incoming_msg = render_to_string('sigmax/actualiseerZaakstatus_Lk01.xml', {
            'zaak_uuid': uuid.uuid4(),
            'tijdstipbericht': '20180927100000',
            'resultaat_omschrijving': 'HALLO',
        })

        # authenticate
        superuser = SuperUserFactory.create()
        self.client.force_authenticate(user=superuser)

        # call our SOAP endpoint
        response = self.client.post(
            SOAP_ENDPOINT, data=incoming_msg, SOAPAction=ACTUALISEER_ZAAK_STATUS_SOAPACTION,
            content_type='text/xml',
        )

        # check that the request was rejected because no signal is present in database
        self.assertEqual(response.status_code, 500)
        self.assertIn('Melding met signal_id', response.content.decode('utf-8', 'strict'))

    def test_with_signal_for_message_wrong_state(self):
        signal = SignalFactoryValidLocation.create()
        self.assertEqual(Signal.objects.count(), 1)

        incoming_msg = render_to_string('sigmax/actualiseerZaakstatus_Lk01.xml', {
            'zaak_uuid': signal.signal_id,
            'tijdstipbericht': '20180927100000',
            'resultaat_omschrijving': 'HALLO',
        })

        # authenticate
        superuser = SuperUserFactory.create()
        self.client.force_authenticate(user=superuser)

        # call our SOAP endpoint
        response = self.client.post(
            SOAP_ENDPOINT, data=incoming_msg, SOAPAction=ACTUALISEER_ZAAK_STATUS_SOAPACTION,
            content_type='text/xml',
        )

        self.assertEqual(response.status_code, 500)
        self.assertIn(str(signal.signal_id), response.content.decode('utf-8', 'strict'))
        self.assertIn('Fo03', response.content.decode('utf-8', 'strict'))

    def test_with_signal_for_message_correct_state(self):
        signal = SignalFactoryValidLocation.create()
        signal.status.state = workflow.VERZONDEN
        signal.status.save()
        signal.refresh_from_db()

        self.assertEqual(Signal.objects.count(), 1)

        incoming_msg = render_to_string('sigmax/actualiseerZaakstatus_Lk01.xml', {
            'zaak_uuid': signal.signal_id,
            'tijdstipbericht': '20180927100000',
            'resultaat_omschrijving': 'HALLO',
        })

        # authenticate
        superuser = SuperUserFactory.create()
        self.client.force_authenticate(user=superuser)

        # call our SOAP endpoint
        response = self.client.post(
            SOAP_ENDPOINT, data=incoming_msg, SOAPAction=ACTUALISEER_ZAAK_STATUS_SOAPACTION,
            content_type='text/xml',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(str(signal.signal_id), response.content.decode('utf-8', 'strict'))
        self.assertIn('Bv03', response.content.decode('utf-8', 'strict'))


class TestProcessTestActualiseerZaakStatus(TestCase):
    def test_reject_not_xml(self):
        test_msg = 'THIS IS NOT XML'
        with self.assertRaises(lxml.etree.XMLSyntaxError):
            _parse_actualiseerZaakstatus_Lk01(test_msg)

    def test_extract_properties(self):
        signal = SignalFactoryValidLocation()
        resultaat = 'Er is gehandhaafd'

        test_msg = render_to_string('sigmax/actualiseerZaakstatus_Lk01.xml', {
            'zaak_uuid': signal.signal_id,
            'resultaat_omschrijving': resultaat
        })
        msg_content = _parse_actualiseerZaakstatus_Lk01(test_msg)

        # test uses knowledge of test XML message content
        self.assertEqual(
            msg_content['zaak_uuid'],
            str(signal.signal_id)
        )
        self.assertEqual(
            msg_content['datum_afgehandeld'],
            '2018092613025501'
        )
        self.assertEqual(
            msg_content['resultaat'],
            resultaat
        )
        self.assertIn('reden', msg_content)
