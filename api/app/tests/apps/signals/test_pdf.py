from django.test import Client, TestCase
from django.urls import reverse

from tests.apps.signals.factories import SignalFactoryValidLocation
from tests.apps.users.factories import UserFactory


class TestPDFView(TestCase):
    def setUp(self):
        self.user = UserFactory.create()  # Normal user without any extra permissions.
        self.user.set_password('test1234')
        self.user.save()

        self.signal = SignalFactoryValidLocation.create()
        self.client = Client()
        self.client.login(username=self.user.username, password='test1234')

    def test_get_pdf(self):
        response = self.client.get(path=reverse(
            'v1:signal-pdf-download',
            kwargs={'pk': self.signal.id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'application/pdf')
        self.assertEqual(
            response.get('Content-Disposition'),
            'attachment; SIA-{}.pdf'.format(self.signal.pk)
        )

    def test_get_pdf_signal_does_not_exists(self):
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

        self.assertEqual(response.status_code, 302)
