from signals.apps.signals.factories import SignalFactory
from tests.test import SIAReadWriteUserMixin, SignalsBaseApiTestCase


class TestPDFView(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    def test_get_pdf(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        signal = SignalFactory.create()
        response = self.client.get(f'/signals/v1/private/signals/{signal.pk}/pdf')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'application/pdf')
        self.assertEqual(response.get('Content-Disposition'), f'attachment;filename="SIA-{signal.pk}.pdf"')

    def test_get_pdf_signal_does_not_exists(self):
        self.client.force_authenticate(user=self.sia_read_write_user)
        response = self.client.get('/signals/v1/private/signals/999/pdf')
        self.assertEqual(response.status_code, 404)

    def test_get_pdf_signal_not_loggedin(self):
        self.client.logout()
        response = self.client.get('/signals/v1/private/signals/999/pdf')
        self.assertEqual(response.status_code, 401)
