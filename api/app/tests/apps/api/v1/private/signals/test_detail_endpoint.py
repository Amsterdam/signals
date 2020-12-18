import os

from django.contrib.auth.models import Permission
from django.test import override_settings

from signals.apps.signals.factories import SignalFactoryValidLocation
from tests.test import SIAReadUserMixin, SIAReadWriteUserMixin, SignalsBaseApiTestCase

THIS_DIR = os.path.dirname(__file__)
JSON_SCHEMA_DIR = os.path.join(THIS_DIR, '..', 'json_schema')


@override_settings(FEATURE_FLAGS={
    'API_SEARCH_ENABLED': False,
    'SEARCH_BUILD_INDEX': False,
    'API_DETERMINE_STADSDEEL_ENABLED': True,
    'API_FILTER_EXTRA_PROPERTIES': True,
    'API_TRANSFORM_SOURCE_BASED_ON_REPORTER': True,
    'API_TRANSFORM_SOURCE_IF_A_SIGNAL_IS_A_CHILD': False,
    'API_VALIDATE_SOURCE_AGAINST_SOURCE_MODEL': False,
    'TASK_UPDATE_CHILDREN_BASED_ON_PARENT': False,
})
class TestPrivateSignalDetailEndpoint(SIAReadUserMixin, SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    endpoint = '/signals/v1/private/signals/'

    detail_json_schema_path = os.path.join(JSON_SCHEMA_DIR, 'get_signals_v1_private_signals_{pk}.json')
    signal_detail_schema = None

    history_json_schema_path = os.path.join(JSON_SCHEMA_DIR, 'get_signals_v1_private_signals_{pk}_history.json')
    signal_history_schema = None

    def setUp(self):
        # Load the JSON Schema's
        self.signal_detail_schema = self.load_json_schema(self.detail_json_schema_path)
        self.signal_history_schema = self.load_json_schema(self.history_json_schema_path)

        # Make sure that we have a user who can read from all Categories
        self.sia_read_write_user.user_permissions.add(Permission.objects.get(codename='sia_can_view_all_categories'))

    def test_get_signal(self):
        """
        The SIA Read write user has a special permission to view all Signals.
        Get the detailed data of a newly created Signal
        """
        self.client.force_authenticate(user=self.sia_read_write_user)

        signal = SignalFactoryValidLocation.create()

        response = self.client.get(f'{self.endpoint}{signal.pk}')
        self.assertEqual(response.status_code, 200)

        # JSONSchema validation
        self.assertJsonSchema(self.signal_detail_schema, response.json())

    def test_get_signal_history(self):
        """
        The SIA Read write user has a special permission to view all Signals.
        Get the history of a newly created Signal
        """
        self.client.force_authenticate(user=self.sia_read_write_user)

        signal = SignalFactoryValidLocation.create()

        response = self.client.get(f'{self.endpoint}{signal.pk}/history')
        self.assertEqual(response.status_code, 200)

        # When a Signal is created it has initially 6 history entries
        self.assertEqual(len(response.json()), 6)

        # JSONSchema validation
        self.assertJsonSchema(self.signal_history_schema, response.json())

    def test_get_signal_does_not_exists(self):
        """
        Signal does not exists
        """
        self.client.force_authenticate(user=self.sia_read_write_user)

        response = self.client.get(f'{self.endpoint}1000000')
        self.assertEqual(response.status_code, 404)

    def test_get_signal_not_logged_in(self):
        """
        Private endpoints are only accessible if a user is logged in
        """
        self.client.logout()

        response = self.client.get(f'{self.endpoint}1')
        self.assertEqual(response.status_code, 401)

    def test_get_signal_history_not_logged_in(self):
        """
        Private endpoints are only accessible if a user is logged in
        """
        self.client.logout()

        response = self.client.get(f'{self.endpoint}1/history')
        self.assertEqual(response.status_code, 401)

    def test_get_signal_not_found_for_user(self):
        """
        The SIA read user has no categories assigned to it. Therefore it is not able to get the details of a Signal
        """
        self.client.force_login(user=self.sia_read_user)

        response = self.client.get(f'{self.endpoint}1')
        self.assertEqual(response.status_code, 401)  # Signal not found for this user

    def test_get_signal_history_not_found_for_user(self):
        """
        The SIA read user has no categories assigned to it. Therefore it is not able to get the details of a Signal
        """
        self.client.force_login(user=self.sia_read_user)

        response = self.client.get(f'{self.endpoint}1/history')
        self.assertEqual(response.status_code, 401)  # Signal not found for this user

    def test_get_parent_signal(self):
        """
        The SIA Read write user has a special permission to view all Signals.
        Get the detailed data of a parent Signal
        """
        self.client.force_authenticate(user=self.sia_read_write_user)

        parent_signal = SignalFactoryValidLocation.create()
        child_signal = SignalFactoryValidLocation.create(parent=parent_signal)

        response = self.client.get(f'{self.endpoint}{parent_signal.pk}')
        self.assertEqual(response.status_code, 200)

        response_data = response.json()

        # JSONSchema validation
        self.assertJsonSchema(self.signal_detail_schema, response_data)

        # Check if there is 1 child signal link present in the '_links'
        self.assertIn('sia:children', response_data['_links'])
        self.assertEqual(len(response_data['_links']['sia:children']), 1)
        self.assertEqual(response_data['_links']['sia:children'][0]['href'],
                         f'http://testserver{self.endpoint}{child_signal.pk}')

    def test_get_child_signal(self):
        """
        The SIA Read write user has a special permission to view all Signals.
        Get the detailed data of a child Signal
        """
        self.client.force_authenticate(user=self.sia_read_write_user)

        parent_signal = SignalFactoryValidLocation.create()
        child_signal = SignalFactoryValidLocation.create(parent=parent_signal)

        response = self.client.get(f'{self.endpoint}{child_signal.pk}')
        self.assertEqual(response.status_code, 200)

        response_data = response.json()

        # JSONSchema validation
        self.assertJsonSchema(self.signal_detail_schema, response_data)

        # Check if the parent signal link present in the '_links'
        self.assertIn('sia:parent', response_data['_links'])
        self.assertEqual(response_data['_links']['sia:parent']['href'],
                         f'http://testserver{self.endpoint}{parent_signal.pk}')
