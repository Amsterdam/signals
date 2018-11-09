from django.test import Client, TestCase
from django.urls import reverse

from tests.apps.signals.factories import SignalFactoryValidLocation


class TestPDFView(TestCase):
    def setUp(self):
        self.client = Client()
        self.signal = SignalFactoryValidLocation.create()

    def test_get_pdf(self):
        response = self.client.get(path=reverse(
            'v1:signal-pdf-download',
            kwargs={'signal_id': self.signal.id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'application/pdf')
        self.assertEquals(
            response.get('Content-Disposition'),
            'attachment; SIA-{}.pdf'.format(self.signal.pk)
        )

    def test_get_pdf_signal_does_not_exists(self):
        response = self.client.get(path=reverse(
            'v1:signal-pdf-download',
            kwargs={'signal_id': 999})
        )

        self.assertEqual(response.status_code, 404)
