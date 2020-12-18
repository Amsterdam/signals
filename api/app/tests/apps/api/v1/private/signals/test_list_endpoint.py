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
class TestPrivateSignalListEndpoint(SIAReadUserMixin, SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    endpoint = '/signals/v1/private/signals/'

    list_json_schema_path = os.path.join(JSON_SCHEMA_DIR, 'get_signals_v1_private_signals.json')
    signal_list_schema = None

    def setUp(self):
        # Load the JSON Schema's
        self.signal_list_schema = self.load_json_schema(self.list_json_schema_path)

        # Make sure that we have a user who can read from all Categories
        self.sia_read_write_user.user_permissions.add(Permission.objects.get(codename='sia_can_view_all_categories'))

    def test_get_signals(self):
        """
        The SIA Read write user has a special permission to view all Signals.
        Get the list data of all Signals
        """
        self.client.force_authenticate(user=self.sia_read_write_user)

        signals = SignalFactoryValidLocation.create_batch(5)

        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 200)

        response_data = response.json()

        # JSONSchema validation
        self.assertJsonSchema(self.signal_list_schema, response_data)

        self.assertEqual(response_data['count'], len(signals))
        self.assertEqual(len(response_data['results']), len(signals))
        self.assertEqual(len(response_data['results']), response_data['count'])

    def test_get_signals_not_logged_in(self):
        """
        Private endpoints are only accessible if a user is logged in
        """
        self.client.logout()

        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 401)
