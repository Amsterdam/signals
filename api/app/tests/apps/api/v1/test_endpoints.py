import os

from django.contrib.auth.models import Permission

from signals.apps.signals.models import Signal
from tests.apps.signals.factories import NoteFactory, SignalFactory
from tests.test import SIAReadWriteUserMixin, SignalsBaseApiTestCase

THIS_DIR = os.path.dirname(__file__)
SIGNALS_TEST_DIR = os.path.join(os.path.split(THIS_DIR)[0], '..', 'signals')


class TestPrivateEndpoints(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    endpoints = [
        '/signals/v1/private/signals/',
    ]

    def setUp(self):
        self.signal = SignalFactory(
            id=1,
            location__id=1,
            status__id=1,
            category_assignment__id=1,
            reporter__id=1,
            priority__id=1
        )

        self.sia_read_write_user.user_permissions.add(Permission.objects.get(codename='sia_can_view_all_categories'))

        # Forcing authentication
        self.client.force_authenticate(user=self.sia_read_write_user)

        # Add one note to the signal
        self.note = NoteFactory(id=1, _signal=self.signal)

    def test_basics(self):
        self.assertEqual(Signal.objects.count(), 1)
        s = Signal.objects.get(pk=1)
        self.assertIsInstance(s, Signal)

    def test_get_lists(self):
        for url in self.endpoints:
            response = self.client.get(url)

            self.assertEqual(response.status_code, 200, 'Wrong response code for {}'.format(url))
            self.assertEqual(response['Content-Type'],
                             'application/json',
                             'Wrong Content-Type for {}'.format(url))
            self.assertIn('count', response.data, 'No count attribute in {}'.format(url))

    def test_get_lists_html(self):
        for url in self.endpoints:
            response = self.client.get('{}?format=api'.format(url))

            self.assertEqual(response.status_code, 200, 'Wrong response code for {}'.format(url))
            self.assertEqual(response['Content-Type'],
                             'text/html; charset=utf-8',
                             'Wrong Content-Type for {}'.format(url))
            self.assertIn('count', response.data, 'No count attribute in {}'.format(url))

    def test_get_detail(self):
        for endpoint in self.endpoints:
            url = f'{endpoint}1'
            response = self.client.get(url)

            self.assertEqual(response.status_code, 200, 'Wrong response code for {}'.format(url))

    def test_get_detail_no_permissions(self):
        self.client.logout()
        self.client.force_login(self.user)

        for endpoint in self.endpoints:
            url = f'{endpoint}1'
            response = self.client.get(url)

            self.assertEqual(response.status_code, 401, 'Wrong response code for {}'.format(url))

        self.client.logout()
        self.client.force_login(self.sia_read_write_user)

    def test_get_detail_no_read_permissions(self):
        self.client.logout()
        self.client.force_login(self.user)

        for endpoint in self.endpoints:
            url = f'{endpoint}1'
            response = self.client.get(url)

            self.assertEqual(response.status_code, 401, 'Wrong response code for {}'.format(url))

        self.client.logout()
        self.client.force_login(self.sia_read_write_user)

    def test_delete_not_allowed(self):
        for endpoint in self.endpoints:
            url = f'{endpoint}1'
            response = self.client.delete(url)

            self.assertEqual(response.status_code, 405, 'Wrong response code for {}'.format(url))
