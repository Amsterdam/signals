import copy
import os
from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.test import override_settings

from signals.apps.signals.factories import (
    CategoryFactory,
    DepartmentFactory,
    SignalFactoryValidLocation
)
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
class TestPrivateSignalUpdateEndpoint(SIAReadUserMixin, SIAReadWriteUserMixin, SignalsBaseApiTestCase):
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

        self.category = CategoryFactory.create()
        self.category_link = f'/signals/v1/public/terms/categories/{self.category.parent.slug}' \
                             f'/sub_categories/{self.category.slug}'

    def test_update_signal_not_logged_in(self):
        """
        Private endpoints are only accessible if a user is logged in
        """
        self.client.logout()

        signal = SignalFactoryValidLocation.create()

        response = self.client.patch(f'{self.endpoint}{signal.pk}', data={}, format='json')
        self.assertEqual(response.status_code, 401)

    def test_put_not_allowed(self):
        """
        Private endpoints do not allow PUT
        """
        self.client.force_authenticate(user=self.superuser)

        signal = SignalFactoryValidLocation.create()

        response = self.client.put(f'{self.endpoint}{signal.pk}', data={}, format='json')
        self.assertEqual(response.status_code, 405)

    @patch("signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address")
    def test_update_location(self, validate_address):
        """
        Update the location of a Signal
        """
        self.client.force_authenticate(user=self.superuser)

        signal = SignalFactoryValidLocation.create()

        patch_data = {
            'location': {
                'geometrie': {
                    'type': 'Point',
                    'coordinates': [4.90022563, 52.36768424]
                },
                'address': {
                    'openbare_ruimte': 'De Ruijterkade',
                    'huisnummer': 36,
                    'huisletter': 'A',
                    'huisnummer_toevoeging': '',
                    'postcode': '1012AA',
                    'woonplaats': 'Amsterdam'
                },
                'extra_properties': None,
                'stadsdeel': 'A',
                'buurt_code': 'A01a'
            }
        }

        validated_address = copy.deepcopy(patch_data['location']['address'])
        validate_address.return_value = validated_address

        # update location
        response = self.client.patch(f'{self.endpoint}{signal.pk}', patch_data, format='json')
        self.assertEqual(response.status_code, 200)

        response_data = response.json()

        # JSONSchema validation
        self.assertJsonSchema(self.signal_detail_schema, response_data)

        signal.refresh_from_db()

        self.assertEqual(signal.location.address, patch_data['location']['address'])
        self.assertEqual(signal.location.buurt_code, patch_data['location']['buurt_code'])
        self.assertEqual(signal.location.created_by, self.superuser.email)
        self.assertIsNotNone(signal.location.extra_properties)
        self.assertEqual(signal.location.stadsdeel, patch_data['location']['stadsdeel'])

        # check that there are two Locations is in the history
        response = self.client.get(f'{self.endpoint}{signal.pk}/history', data={'what': 'UPDATE_LOCATION'})

        # JSONSchema validation
        response_data = response.json()
        self.assertJsonSchema(self.signal_history_schema, response_data)

        # The original location and the changed location should be in the history
        self.assertEqual(len(response_data), 2)

    @patch("signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address")
    def test_update_location_no_address(self, validate_address):
        """
        Update the location of a Signal without an address
        """
        self.client.force_authenticate(user=self.superuser)

        signal = SignalFactoryValidLocation.create()

        patch_data = {
            'location': {
                'geometrie': {
                    'type': 'Point',
                    'coordinates': [4.90022563, 52.36768424]
                },
                'extra_properties': None,
                'stadsdeel': 'A',
                'buurt_code': 'A01a'
            }
        }

        # update location
        response = self.client.patch(f'{self.endpoint}{signal.pk}', patch_data, format='json')
        self.assertEqual(response.status_code, 200)
        validate_address.assert_not_called()

        response_data = response.json()

        # JSONSchema validation
        self.assertJsonSchema(self.signal_detail_schema, response_data)

        signal.refresh_from_db()

        self.assertIsNone(signal.location.address)
        self.assertEqual(signal.location.buurt_code, patch_data['location']['buurt_code'])
        self.assertEqual(signal.location.created_by, self.superuser.email)
        self.assertIsNone(signal.location.extra_properties)
        self.assertEqual(signal.location.stadsdeel, patch_data['location']['stadsdeel'])

        # check that there are two Locations is in the history
        response = self.client.get(f'{self.endpoint}{signal.pk}/history', data={'what': 'UPDATE_LOCATION'})

        # JSONSchema validation
        response_data = response.json()
        self.assertJsonSchema(self.signal_history_schema, response_data)

        # The original location and the changed location should be in the history
        self.assertEqual(len(response_data), 2)

    @patch("signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address")
    def test_update_location_no_coordinates(self, validate_address):
        """
        Update the location of a Signal without an location is not allowed
        """
        self.client.force_authenticate(user=self.superuser)

        signal = SignalFactoryValidLocation.create()

        patch_data = {
            'location': {
                'address': {
                    'openbare_ruimte': 'De Ruijterkade',
                    'huisnummer': 36,
                    'huisletter': 'A',
                    'huisnummer_toevoeging': '',
                    'postcode': '1012AA',
                    'woonplaats': 'Amsterdam'
                },
                'extra_properties': None,
                'stadsdeel': 'A',
                'buurt_code': 'A01a'
            }
        }

        # update location
        response = self.client.patch(f'{self.endpoint}{signal.pk}', patch_data, format='json')
        self.assertEqual(response.status_code, 400)
        validate_address.assert_not_called()

        # check that there are two Locations is in the history
        response = self.client.get(f'{self.endpoint}{signal.pk}/history', data={'what': 'UPDATE_LOCATION'})

        # JSONSchema validation
        response_data = response.json()
        self.assertJsonSchema(self.signal_history_schema, response_data)

        # Only the original location and no changed location should be in the history
        self.assertEqual(len(response_data), 1)

    def test_update_status(self):
        """
        Update the status of a Signal
        """
        self.client.force_authenticate(user=self.superuser)

        signal = SignalFactoryValidLocation.create()

        patch_data = {
            'status': {
                'text': 'Update to "In behandeling"',
                'state': 'b'
            }
        }

        # update status
        response = self.client.patch(f'{self.endpoint}{signal.pk}', patch_data, format='json')
        self.assertEqual(response.status_code, 200)

        response_data = response.json()

        # JSONSchema validation
        self.assertJsonSchema(self.signal_detail_schema, response_data)

        # check that there are two Locations is in the history
        response = self.client.get(f'{self.endpoint}{signal.pk}/history', data={'what': 'UPDATE_STATUS'})

        # JSONSchema validation
        response_data = response.json()
        self.assertJsonSchema(self.signal_history_schema, response_data)

        # The original status and the changed status should be in the history
        self.assertEqual(len(response_data), 2)

    def test_update_status_invalid_workflow(self):
        """
        Update the status of a Signal
        """
        self.client.force_authenticate(user=self.superuser)

        signal = SignalFactoryValidLocation.create(status__state='o')

        patch_data = {
            'status': {
                'text': 'Update to "In behandeling" should not be allowed when the current status is "Afgehandeld"',
                'state': 'b'
            }
        }

        # update status
        response = self.client.patch(f'{self.endpoint}{signal.pk}', patch_data, format='json')
        self.assertEqual(response.status_code, 400)

        # check that there are two Locations is in the history
        response = self.client.get(f'{self.endpoint}{signal.pk}/history', data={'what': 'UPDATE_STATUS'})

        # JSONSchema validation
        response_json = response.json()
        self.assertJsonSchema(self.signal_history_schema, response_json)

        # Only the original status and not the changed status should be in the history
        self.assertEqual(len(response.json()), 1)

    def test_send_to_sigmax_no_permission(self):
        self.client.force_authenticate(user=self.sia_read_user)

        signal = SignalFactoryValidLocation.create(status__state='o')

        patch_data = {
            'status': {
                'state': 'ready to send',
                'text': 'Te verzenden naar THOR',
                'target_api': 'sigmax',
            }
        }

        # update status
        response = self.client.patch(f'{self.endpoint}{signal.pk}', patch_data, format='json')
        self.assertEqual(response.status_code, 403)

    def test_update_status_with_required_text(self):
        """
        A Status update to 'afgehandeld' (o) requires text.
        When no text is supplied, a 400 should be returned
        """
        self.client.force_authenticate(user=self.superuser)

        signal = SignalFactoryValidLocation.create(status__state='o')

        patch_data = {
            'status': {
                'state': 'o',
                'text': None,  # Text is required in this test
            }
        }

        # update status
        response = self.client.patch(f'{self.endpoint}{signal.pk}', patch_data, format='json')
        self.assertEqual(response.status_code, 400)

    def test_update_category_assignment(self):
        self.client.force_authenticate(user=self.superuser)

        signal = SignalFactoryValidLocation.create()

        patch_data = {
            'category': {
                'text': 'Update the category assignment',
                'category_url': self.category_link
            }
        }

        # update status
        response = self.client.patch(f'{self.endpoint}{signal.pk}', patch_data, format='json')
        self.assertEqual(response.status_code, 200)

        response_data = response.json()

        # JSONSchema validation
        self.assertJsonSchema(self.signal_detail_schema, response_data)

        signal.refresh_from_db()

        self.assertEqual(signal.categories.count(), 2)
        self.assertEqual(signal.category_assignment.category.pk, self.category.pk)
        self.assertEqual(signal.category_assignment.created_by, self.superuser.email)
        self.assertIsNone(signal.category_assignment.extra_properties)
        self.assertEqual(signal.category_assignment.text, patch_data['category']['text'])

        # check that there are two category assignments is in the history
        response = self.client.get(f'{self.endpoint}{signal.pk}/history', data={'what': 'UPDATE_CATEGORY_ASSIGNMENT'})

        # JSONSchema validation
        response_data = response.json()
        self.assertJsonSchema(self.signal_history_schema, response_data)

        # The original category assignment and the category assignment should be in the history
        self.assertEqual(len(response_data), 2)
        self.assertEqual(response_data[0]['description'], patch_data['category']['text'])

    def test_update_category_assignment_same_category(self):
        self.client.force_authenticate(user=self.superuser)

        signal = SignalFactoryValidLocation.create()

        patch_data = {
            'category': {
                'text': 'Update the category assignment',
                'category_url': '/signals/v1/public/terms/categories/'
                                f'{signal.category_assignment.category.parent.slug}/sub_categories/'
                                f'{signal.category_assignment.category.slug}'
            }
        }

        # update status
        response = self.client.patch(f'{self.endpoint}{signal.pk}', patch_data, format='json')
        self.assertEqual(response.status_code, 200)

        response_data = response.json()

        # JSONSchema validation
        self.assertJsonSchema(self.signal_detail_schema, response_data)

        signal.refresh_from_db()

        self.assertEqual(signal.categories.count(), 1)
        self.assertEqual(signal.category_assignment.category.pk, signal.category_assignment.category.pk)

        # check that there is only one category assignment in the history
        response = self.client.get(f'{self.endpoint}{signal.pk}/history', data={'what': 'UPDATE_CATEGORY_ASSIGNMENT'})

        # JSONSchema validation
        response_data = response.json()
        self.assertJsonSchema(self.signal_history_schema, response_data)

        # Only the original category assignment and not the category assignment should be in the history
        self.assertEqual(len(response_data), 1)

    def test_update_priority(self):
        self.client.force_authenticate(user=self.superuser)

        signal = SignalFactoryValidLocation.create()

        patch_data = {
            'priority': {
                'priority': 'high'
            }
        }

        # update priority
        response = self.client.patch(f'{self.endpoint}{signal.pk}', patch_data, format='json')
        self.assertEqual(response.status_code, 200)

        response_data = response.json()

        # JSONSchema validation
        self.assertJsonSchema(self.signal_detail_schema, response_data)

        signal.refresh_from_db()

        self.assertEqual(signal.priority.priority, patch_data['priority']['priority'])
        self.assertEqual(signal.priority.created_by, self.superuser.email)

        # check that there are two Locations is in the history
        response = self.client.get(f'{self.endpoint}{signal.pk}/history', data={'what': 'UPDATE_PRIORITY'})

        # JSONSchema validation
        response_data = response.json()
        self.assertJsonSchema(self.signal_history_schema, response_data)

        # The original priority and the new priority should be in the history
        self.assertEqual(len(response_data), 2)

    def test_update_type(self):
        self.client.force_authenticate(user=self.superuser)

        signal = SignalFactoryValidLocation.create()

        patch_data = {
            'type': {
                'code': 'SIG'
            }
        }

        # update priority
        response = self.client.patch(f'{self.endpoint}{signal.pk}', patch_data, format='json')
        self.assertEqual(response.status_code, 200)

        response_data = response.json()

        # JSONSchema validation
        self.assertJsonSchema(self.signal_detail_schema, response_data)

        signal.refresh_from_db()

        self.assertEqual(signal.type_assignment.name, patch_data['type']['code'])
        self.assertEqual(signal.type_assignment.created_by, self.superuser.email)

        # check that there are two Locations is in the history
        response = self.client.get(f'{self.endpoint}{signal.pk}/history', data={'what': 'UPDATE_TYPE_ASSIGNMENT'})

        # JSONSchema validation
        response_data = response.json()
        self.assertJsonSchema(self.signal_history_schema, response_data)

        # The original type and the new type should be in the history
        self.assertEqual(len(response_data), 2)

    def test_update_type_invalid_code(self):
        self.client.force_authenticate(user=self.superuser)

        signal = SignalFactoryValidLocation.create()

        patch_data = {
            'type': {
                'code': 'GARBAGE'
            }
        }

        # update priority
        response = self.client.patch(f'{self.endpoint}{signal.pk}', patch_data, format='json')
        self.assertEqual(response.status_code, 400)

        signal.refresh_from_db()

        self.assertNotEqual(signal.type_assignment.name, patch_data['type']['code'])

        # check that there are two Locations is in the history
        response = self.client.get(f'{self.endpoint}{signal.pk}/history', data={'what': 'UPDATE_TYPE_ASSIGNMENT'})

        # JSONSchema validation
        response_data = response.json()
        self.assertJsonSchema(self.signal_history_schema, response_data)

        # Only the original type and not the updated type should be in the history
        self.assertEqual(len(response_data), 1)

    @patch("signals.apps.api.v1.serializers.PrivateSignalSerializerDetail.update")
    def test_patch_django_validation_error_to_drf_validation_error(self, mock):
        self.client.force_authenticate(user=self.superuser)

        mock.side_effect = ValidationError('this is a test')

        signal = SignalFactoryValidLocation.create()

        response = self.client.patch(f'{self.endpoint}{signal.pk}', data={}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(1, len(response.json()))
        self.assertEqual('this is a test', response.json()[0])

    def test_update_directing_departments_on_parent_signal(self):
        # While the split functionality is removed from SIA/Signalen there can
        # stil be `signal.Signal` instances that were split, and still have to
        # be handled or be shown in historical data.
        self.client.force_authenticate(user=self.superuser)

        parent_signal = SignalFactoryValidLocation.create(status__state='s')
        SignalFactoryValidLocation.create(parent=parent_signal)

        department = DepartmentFactory.create()

        patch_data = {
            'directing_departments': [
                {
                    'id': department.pk
                },
            ]
        }

        # update priority
        response = self.client.patch(f'{self.endpoint}{parent_signal.pk}', patch_data, format='json')
        self.assertEqual(response.status_code, 200)

        response_data = response.json()

        # JSONSchema validation
        self.assertJsonSchema(self.signal_detail_schema, response_data)

        self.assertIn('directing_departments', response_data)
        self.assertEqual(len(response_data['directing_departments']), len(patch_data['directing_departments']))
        self.assertEqual(response_data['directing_departments'][0]['id'], department.pk)
        self.assertEqual(response_data['directing_departments'][0]['code'], department.code)
        self.assertEqual(response_data['directing_departments'][0]['name'], department.name)
        self.assertEqual(response_data['directing_departments'][0]['is_intern'], department.is_intern)

        parent_signal.refresh_from_db()

        self.assertEqual(parent_signal.signal_departments.filter(relation_type='directing').count(), 1)
        self.assertIsNotNone(parent_signal.directing_departments_assignment)
        self.assertEqual(parent_signal.directing_departments_assignment.departments.count(), 1)
        self.assertEqual(parent_signal.directing_departments_assignment.departments.first().id, department.pk)

        # check that there are two Locations is in the history
        response = self.client.get(f'{self.endpoint}{parent_signal.pk}/history', data={
            'what': 'UPDATE_DIRECTING_DEPARTMENTS_ASSIGNMENT'
        })

        # JSONSchema validation
        response_data = response.json()
        self.assertJsonSchema(self.signal_history_schema, response_data)

        # The directing department should show up in the history
        self.assertEqual(len(response_data), 1)
