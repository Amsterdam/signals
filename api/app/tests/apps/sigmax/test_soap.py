import lxml
from django.template.loader import render_to_string
from rest_framework.test import APITestCase
from django.test import TestCase
from rest_framework.test import APIClient

from signals.apps.sigmax.views import (
    _parse_actualiseerZaakstatus_Lk01, ACTUALISEER_ZAAK_STATUS_SOAPACTION)
from tests.apps.users.factories import SuperUserFactory



class TestActualiseerZaakstatus(APITestCase):
    def test_send_example(self):
        payload = render_to_string('sigmax/example-actualiseerZaakstatus_Lk01.xml')

        superuser = SuperUserFactory.create()
        self.client.force_authenticate(user=superuser)
        response = self.client.post(
            '/signals/sigmax/soap',
            data=payload,
            content_type='application/xml',
            **{'SOAPAction': ACTUALISEER_ZAAK_STATUS_SOAPACTION}
        )



class TestProcessTestActualiseerZaakStatus(TestCase):
    def test_reject_not_xml(self):
        test_msg = 'THIS IS NOT XML'
        with self.assertRaises(lxml.etree.XMLSyntaxError):
            _parse_actualiseerZaakstatus_Lk01(test_msg)

    def test_extract_properties(self):
        test_msg = render_to_string('sigmax/example-actualiseerZaakstatus_Lk01.xml')
        msg_content = _parse_actualiseerZaakstatus_Lk01(test_msg)

        # test uses knowledge of test XML message content
        self.assertEqual(
            msg_content['zaak_uuid'],
            'ed919712-d026-4949-a51e-5a8b60141a0d'
        )
        self.assertEqual(
            msg_content['datum_afgehandeld'],
            '2018070409102946'
        )
        self.assertEqual(
            msg_content['resultaat'],
            'Geseponeerd'
        )
        self.assertIn('reden', msg_content)

