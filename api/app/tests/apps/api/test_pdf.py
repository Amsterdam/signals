from django.urls import reverse

from tests.apps.signals.factories import SignalFactory
from tests.test import SIAReadWriteUserMixin, SignalsBaseApiTestCase


class TestPDFView(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    def setUp(self):
        self.signal = SignalFactory.create()

    def test_get_pdf(self):
        self.client.force_authenticate(user=self.sia_read_write_user)
        response = self.client.get(path=reverse(
            'v1:signal-pdf-download',
            kwargs={'pk': self.signal.id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'application/pdf')
        self.assertEqual(
            response.get('Content-Disposition'),
            'attachment; filename="SIA-{}.pdf"'.format(self.signal.pk)
        )

    def test_get_pdf_signal_does_not_exists(self):
        self.client.force_authenticate(user=self.sia_read_write_user)
        response = self.client.get(path=reverse(
            'v1:signal-pdf-download',
            kwargs={'pk': 999})
        )

        self.assertEqual(response.status_code, 404)

    def test_get_pdf_signal_not_loggedin(self):
        self.client.logout()

        response = self.client.get(path=reverse(
            'v1:signal-pdf-download',
            kwargs={'pk': 999})
        )

        self.assertEqual(response.status_code, 401)
