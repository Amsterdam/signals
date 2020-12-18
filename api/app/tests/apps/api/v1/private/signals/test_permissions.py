import copy
import os
from unittest.mock import patch

from django.test import override_settings
from django.utils import timezone
from freezegun import freeze_time
from rest_framework import status

from signals.apps.signals.factories import (
    CategoryFactory,
    DepartmentFactory,
    ParentCategoryFactory,
    SignalFactoryValidLocation
)
from signals.apps.signals.models import Signal
from tests.test import SIAReadUserMixin, SIAReadWriteUserMixin, SignalsBaseApiTestCase

THIS_DIR = os.path.dirname(__file__)
SIGNALS_TEST_DIR = os.path.join(os.path.split(THIS_DIR)[0], '..', 'signals')


@freeze_time('2019-11-01 12:00:00', tz_offset=1)
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
class TestPrivateSignalViewSetPermissions(SIAReadUserMixin, SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    endpoint = '/signals/v1/private/signals/'

    def setUp(self):
        department = DepartmentFactory.create(code='TST', name='Department for testing #1', is_intern=False)

        parent_category = ParentCategoryFactory.create()
        self.subcategory = CategoryFactory.create(parent=parent_category, departments=[department, ])
        self.subcategory_2 = CategoryFactory.create(parent=parent_category)

        self.signal = SignalFactoryValidLocation.create(category_assignment__category=self.subcategory)
        self.signal_other_category = SignalFactoryValidLocation.create(category_assignment__category=self.subcategory_2)

        parent_category_url = f'/signals/v1/public/terms/categories/{parent_category.slug}'
        self.link_subcategory = f'{parent_category_url}/sub_categories/{self.subcategory.slug}'
        self.link_subcategory_2 = f'{parent_category_url}/sub_categories/{self.subcategory_2.slug}'

        self.sia_read_write_user.profile.departments.add(department)

    def test_create_initial_forbidden(self):
        self.client.force_authenticate(user=self.sia_read_user)

        post_data = {
            'text': 'Er liggen losse stoeptegels op het trottoir',
            'category': {
                'sub_category': self.link_subcategory,
            },
            'location': {},
            'reporter': {},
            'incident_date_start': timezone.now(),
            'source': 'test-api',
        }
        response = self.client.post(self.endpoint, data=post_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_initial(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        post_data = {
            'text': 'Er liggen losse stoeptegels op het trottoir',
            'category': {
                'sub_category': self.link_subcategory,
            },
            'location': {
                'geometrie': {
                    'type': 'Point',
                    'coordinates': [4.90022563, 52.36768424]
                },
            },
            'reporter': {},
            'incident_date_start': timezone.now(),
            'source': 'test-api',
        }
        response = self.client.post(self.endpoint, data=post_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_note_forbidden(self):
        self.client.force_authenticate(user=self.sia_read_user)

        patch_data = {'notes': [{'text': 'This is a text for a note.'}]}
        response = self.client.patch(f'{self.endpoint}{self.signal.pk}', data=patch_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_note(self):
        self.client.force_authenticate(user=self.sia_read_write_user)
        self.assertEqual(self.signal.notes.count(), 0)

        patch_data = {'notes': [{'text': 'This is a text for a note.'}]}
        response = self.client.patch(f'{self.endpoint}{self.signal.pk}', data=patch_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.signal.refresh_from_db()

        self.assertEqual(self.signal.notes.count(), 1)
        self.assertEqual(self.signal.notes.first().created_by, self.sia_read_write_user.email)

    def test_change_status_forbidden(self):
        self.client.force_authenticate(user=self.sia_read_user)

        patch_data = {
            'status': {
                'text': 'Test status update',
                'state': 'b'
            }
        }
        response = self.client.patch(f'{self.endpoint}{self.signal.pk}', data=patch_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_change_status(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        patch_data = {
            'status': {
                'text': 'Test status update',
                'state': 'b'
            }
        }
        response = self.client.patch(f'{self.endpoint}{self.signal.pk}', data=patch_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.signal.refresh_from_db()

        self.assertEqual(self.signal.status.state, 'b')
        self.assertEqual(self.signal.status.user, self.sia_read_write_user.email)

    def test_change_category_forbidden(self):
        self.client.force_authenticate(user=self.sia_read_user)

        patch_data = {
            'category': {
                'text': 'Update category test',
                'sub_category': self.link_subcategory_2
            }
        }
        response = self.client.patch(f'{self.endpoint}{self.signal.pk}', data=patch_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_change_category(self):
        self.client.force_authenticate(user=self.sia_read_write_user)
        self.assertEqual(self.signal.category_assignment.category.pk, self.subcategory.pk)

        patch_data = {
            'category': {
                'text': 'Update category test',
                'sub_category': self.link_subcategory_2
            }
        }
        response = self.client.patch(f'{self.endpoint}{self.signal.pk}', data=patch_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.signal.refresh_from_db()

        self.assertEqual(self.signal.category_assignment.category.pk, self.subcategory_2.pk)
        self.assertEqual(self.signal.category_assignment.created_by, self.sia_read_write_user.email)

    @patch('signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address')
    def test_update_location(self, validate_address):
        self.client.force_authenticate(user=self.sia_read_write_user)

        patch_data = {
            'location': {
                'geometrie': {
                    'type': 'Point',
                    'coordinates': [
                        4.90022563,
                        52.36768424
                    ]
                },
                'address': {
                    'openbare_ruimte': 'De Ruijterkade',
                    'huisnummer': '36',
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

        response = self.client.patch(f'{self.endpoint}{self.signal.pk}', patch_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.signal.refresh_from_db()

        self.assertEqual(self.signal.location.created_by, self.sia_read_write_user.email)

    def test_create_initial_role_based_permission(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        post_data = {
            'text': 'Er liggen losse stoeptegels op het trottoir',
            'category': {
                'sub_category': self.link_subcategory,
            },
            'location': {
                'geometrie': {
                    'type': 'Point',
                    'coordinates': [4.90022563, 52.36768424]
                },
            },
            'reporter': {},
            'incident_date_start': timezone.now(),
            'source': 'test-api',
        }
        response = self.client.post(self.endpoint, data=post_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_multiple_actions_role_based_permission(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        patch_data = {
            'status': {
                'text': 'Test status update',
                'state': 'b'
            },
            'notes': [{
                'text': 'This is a text for a note.'
            }],
            'category': {
                'text': 'Update category test',
                'sub_category': self.link_subcategory_2
            },
            'location': {
                'geometrie': {
                    'type': 'Point',
                    'coordinates': [
                        4.90022563,
                        52.36768424
                    ]
                },
                'address': {
                    'openbare_ruimte': 'De Ruijterkade',
                    'huisnummer': '36',
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
        response = self.client.patch(f'{self.endpoint}{self.signal.pk}', data=patch_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_category_method_not_allowed(self):
        self.assertEqual(self.signal.category_assignment.category.pk, self.subcategory.pk)

        self.client.force_authenticate(user=self.sia_read_write_user)

        patch_data = {
            'category': {
                'text': 'Update category test',
                'sub_category': self.link_subcategory_2
            }
        }
        response = self.client.delete(f'{self.endpoint}{self.signal.pk}', data=patch_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        self.signal.refresh_from_db()

        self.assertEqual(self.signal.category_assignment.category.pk, self.subcategory.pk)

    def test_get_signals(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['count'], Signal.objects.filter_for_user(user=self.sia_read_write_user).count())
        self.assertNotEqual(data['count'], Signal.objects.count())
        self.assertEqual(2, Signal.objects.count())

    def test_change_category_to_other_category_in_other_department(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['count'], Signal.objects.filter_for_user(user=self.sia_read_write_user).count())
        self.assertNotEqual(data['count'], Signal.objects.count())
        self.assertEqual(2, Signal.objects.count())

        patch_data = {'category': {'text': 'Update category test', 'sub_category': self.link_subcategory_2}}
        response = self.client.patch(f'{self.endpoint}{self.signal.pk}', data=patch_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data['count'], 0)
        self.assertEqual(data['count'], Signal.objects.filter_for_user(user=self.sia_read_write_user).count())
        self.assertNotEqual(data['count'], Signal.objects.count())
        self.assertEqual(2, Signal.objects.count())

    def test_get_signal_not_my_department(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        signal = SignalFactoryValidLocation.create(category_assignment__category=self.subcategory_2)

        response = self.client.get(f'{self.endpoint}{signal.pk}')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_change_signal_not_my_department(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        signal = SignalFactoryValidLocation.create(category_assignment__category=self.subcategory_2)

        patch_data = {'category': {'text': 'Update category test', 'sub_category': self.link_subcategory_2}}
        response = self.client.patch(f'{self.endpoint}{signal.pk}', data=patch_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
