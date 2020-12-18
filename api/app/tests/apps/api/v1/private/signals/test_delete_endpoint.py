from rest_framework import status

from signals.apps.signals.factories import SignalFactory
from signals.apps.signals.models import Signal
from tests.test import SIAReadWriteUserMixin, SignalsBaseApiTestCase


class TestPrivateSignalViewSetCreate(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    endpoint = '/signals/v1/private/signals/'

    def test_delete_signal_not_logged_in(self):
        self.client.logout()

        signal = SignalFactory.create()
        self.assertEqual(Signal.objects.count(), 1)

        response = self.client.delete(f'{self.endpoint}{signal.pk}', format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Signal.objects.count(), 1)

    def test_delete_signal_not_allowed(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        signal = SignalFactory.create()
        self.assertEqual(Signal.objects.count(), 1)

        response = self.client.delete(f'{self.endpoint}{signal.pk}', format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(Signal.objects.count(), 1)
