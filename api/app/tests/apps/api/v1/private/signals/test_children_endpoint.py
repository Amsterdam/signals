from django.contrib.auth.models import Permission

from signals.apps.signals.factories import SignalFactoryValidLocation
from tests.test import SIAReadUserMixin, SIAReadWriteUserMixin, SignalsBaseApiTestCase


class TestSignalChildrenEndpoint(SIAReadUserMixin, SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    endpoint = '/signals/v1/private/signals/'

    def setUp(self):
        # Make sure that we have a user who can read from all Categories
        self.sia_read_write_user.user_permissions.add(Permission.objects.get(codename='sia_can_view_all_categories'))

    def test_not_logged_in(self):
        """
        Private endpoints are only accessible if a user is logged in
        """
        self.client.logout()

        response = self.client.get(f'{self.endpoint}1/children/')
        self.assertEqual(response.status_code, 401)

    def test_get_children(self):
        """
        The SIA Read write user has a special permission to view all Signals.
        Get the children data of a parent Signal
        """
        self.client.force_authenticate(user=self.sia_read_write_user)

        parent_signal = SignalFactoryValidLocation.create()
        child_signal = SignalFactoryValidLocation.create(parent=parent_signal)
        parent_signal.refresh_from_db()

        # Check that we can access a parent signal's children.
        response = self.client.get(f'{self.endpoint}{parent_signal.pk}/children/')
        self.assertEqual(response.status_code, 200)

        response_data = response.json()

        self.assertEqual(response_data['count'], parent_signal.children.count())
        self.assertEqual(len(response_data['results']), parent_signal.children.count())
        self.assertEqual(response_data['count'], len(response_data['results']))

        self.assertEqual(response_data['results'][0]['id'], child_signal.pk)

    def test_not_found_for_user(self):
        """
        The SIA read user has no categories assigned to it. Therefore it is not able to get the children of a Signal
        """
        self.client.force_authenticate(user=self.sia_read_user)

        parent_signal = SignalFactoryValidLocation.create()
        SignalFactoryValidLocation.create(parent=parent_signal)

        response = self.client.get(f'{self.endpoint}{parent_signal.pk}/children/')
        self.assertEqual(response.status_code, 403)
