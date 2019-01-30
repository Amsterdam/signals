import json
import os
from unittest import skip
from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.http import urlencode
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from signals import API_VERSIONS
from signals.apps.signals import workflow
from signals.apps.signals.address.validation import (
    AddressValidationUnavailableException,
    NoResultsException
)
from signals.apps.signals.models import History, MainCategory, Signal, SubCategory
from signals.utils.version import get_version
from tests.apps.signals.factories import (
    MainCategoryFactory,
    NoteFactory,
    SignalFactory,
    SignalFactoryValidLocation,
    SignalFactoryWithImage,
    SubCategoryFactory
)
from tests.apps.users.factories import SuperUserFactory, UserFactory

THIS_DIR = os.path.dirname(__file__)


class TestAPIRoot(APITestCase):

    def test_http_header_api_version(self):
        response = self.client.get('/signals/v1/')

        self.assertEqual(response['X-API-Version'], get_version(API_VERSIONS['v1']))


class TestCategoryTermsEndpoints(APITestCase):
    fixtures = ['categories.json', ]

    def test_category_list(self):
        # Asserting that we've 9 `MainCategory` objects loaded from the json fixture.
        self.assertEqual(MainCategory.objects.count(), 9)

        url = '/signals/v1/public/terms/categories/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data['results']), 9)

    def test_category_detail(self):
        # Asserting that we've 13 sub categories for our main category "Afval".
        main_category = MainCategoryFactory.create(name='Afval')
        self.assertEqual(main_category.sub_categories.count(), 13)

        url = '/signals/v1/public/terms/categories/{slug}'.format(slug=main_category.slug)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['name'], 'Afval')
        self.assertEqual(len(data['sub_categories']), 13)

    def test_sub_category_detail(self):
        sub_category = SubCategoryFactory.create(name='Grofvuil', main_category__name='Afval')

        url = '/signals/v1/public/terms/categories/{slug}/sub_categories/{sub_slug}'.format(
            slug=sub_category.main_category.slug,
            sub_slug=sub_category.slug)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['name'], 'Grofvuil')
        self.assertIn('is_active', data)


class TestPrivateEndpoints(APITestCase):
    """Test whether the endpoints in V1 API """
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

        self.user_no_permissions = UserFactory.create()

        read_permission = Permission.objects.get(codename='sia_read')
        write_permission = Permission.objects.get(codename='sia_write')

        self.user_with_permissions = UserFactory.create()
        self.user_with_permissions.user_permissions.add(read_permission)
        self.user_with_permissions.user_permissions.add(write_permission)

        self.user_no_read_permissions = UserFactory.create()
        self.user_no_read_permissions.user_permissions.add(write_permission)

        self.user_no_write_permissions = UserFactory.create()
        self.user_no_write_permissions.user_permissions.add(read_permission)

        # Forcing authentication
        self.client.force_authenticate(user=self.user_with_permissions)

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
        self.client.force_login(self.user_no_permissions)

        for endpoint in self.endpoints:
            url = f'{endpoint}1'
            response = self.client.get(url)

            self.assertEqual(response.status_code, 401, 'Wrong response code for {}'.format(url))

        self.client.logout()
        self.client.force_login(self.user_with_permissions)

    def test_get_detail_no_read_permissions(self):
        self.client.logout()
        self.client.force_login(self.user_no_read_permissions)

        for endpoint in self.endpoints:
            url = f'{endpoint}1'
            response = self.client.get(url)

            self.assertEqual(response.status_code, 401, 'Wrong response code for {}'.format(url))

        self.client.logout()
        self.client.force_login(self.user_with_permissions)

    def test_delete_not_allowed(self):
        for endpoint in self.endpoints:
            url = f'{endpoint}1'
            response = self.client.delete(url)

            self.assertEqual(response.status_code, 405, 'Wrong response code for {}'.format(url))


class TestHistoryAction(APITestCase):
    def setUp(self):
        self.signal = SignalFactory.create()
        self.superuser = SuperUserFactory(username='superuser@example.com')
        self.user = UserFactory(username='user@example.com')

    def test_history_action_present(self):
        response = self.client.get(f'/signals/v1/private/signals/{self.signal.id}/history')
        self.assertEqual(response.status_code, 401)

        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(f'/signals/v1/private/signals/{self.signal.id}/history')
        self.assertEqual(response.status_code, 200)

    def test_history_endpoint_rendering(self):
        history_entries = History.objects.filter(_signal__id=self.signal.pk)

        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(f'/signals/v1/private/signals/{self.signal.id}/history')
        self.assertEqual(response.status_code, 200)

        result = response.json()
        self.assertEqual(len(result), history_entries.count())

    def test_history_entry_contents(self):
        keys = ['identifier', 'when', 'what', 'action', 'description', 'who', '_signal']

        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(f'/signals/v1/private/signals/{self.signal.id}/history')
        self.assertEqual(response.status_code, 200)

        for entry in response.json():
            for k in keys:
                self.assertIn(k, entry)

    def test_update_shows_up(self):
        # Get a baseline for the Signal history
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(f'/signals/v1/private/signals/{self.signal.id}/history')
        n_entries = len(response.json())
        self.assertEqual(response.status_code, 200)

        # Update the Signal status, and ...
        status = Signal.actions.update_status(
            {
                'text': 'DIT IS EEN TEST',
                'state': workflow.AFGEHANDELD,
                'user': self.user,
            },
            self.signal
        )

        # ... check that the new status shows up as most recent entry in history.
        response = self.client.get(f'/signals/v1/private/signals/{self.signal.id}/history')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), n_entries + 1)

        new_entry = response.json()[0]  # most recent status should be first
        self.assertEqual(new_entry['who'], self.user.username)
        self.assertEqual(new_entry['description'], status.text)


class TestImageUpload(APITestCase):
    def setUp(self):
        self.signal = SignalFactory.create()
        self.superuser = SuperUserFactory(username='superuser@example.com')

        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )

    def test_authenticated_upload(self):
        # images are attached to pre-existing Signals
        endpoint = f'/signals/v1/private/signals/{self.signal.id}/image'
        image = SimpleUploadedFile('image.gif', self.small_gif, content_type='image/gif')

        self.client.force_authenticate(user=self.superuser)
        response = self.client.post(
            endpoint,
            data={'image': image},
            # format='multipart'
        )

        self.assertEqual(response.status_code, 202)


class TestPrivateSignalViewSet(APITestCase):
    """
    Test basic properties of the V1 /signals/v1/private/signals endpoint.

    Note: we check both the list endpoint and associated detail endpoint.
    """

    def setUp(self):
        # initialize database with 2 Signals
        self.signal_no_image = SignalFactoryValidLocation.create()
        self.signal_with_image = SignalFactoryWithImage.create()

        self.superuser = SuperUserFactory.create(
            email='superuser@example.com',
            username='superuser@example.com',
        )
        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )

        # No URL reversing here, these endpoints are part of the spec (and thus
        # should not change).
        self.list_endpoint = '/signals/v1/private/signals/'
        self.detail_endpoint = '/signals/v1/private/signals/{pk}'
        self.history_endpoint = '/signals/v1/private/signals/{pk}/history'
        self.history_image = '/signals/v1/private/signals/{pk}/image'

        # Create a special pair of sub and main categories for testing (insulate our tests
        # from future changes in categories).
        # TODO: add to factories.
        self.test_cat_main = MainCategory(name='testmain')
        self.test_cat_main.save()
        self.test_cat_sub = SubCategory(
            main_category=self.test_cat_main,
            name='testsub',
            handling=SubCategory.HANDLING_A3DMC,
        )
        self.test_cat_sub.save()
        self.link_test_cat_sub = reverse(
            'v1:sub-category-detail', kwargs={
                'slug': self.test_cat_main.slug,
                'sub_slug': self.test_cat_sub.slug,
            }
        )

        # Load fixture of initial data, augment with above test categories.
        fixture_file = os.path.join(THIS_DIR, 'create_initial.json')
        with open(fixture_file, 'r') as f:
            self.create_initial_data = json.load(f)
        self.create_initial_data['category'] = {'sub_category': self.link_test_cat_sub}

    # -- Read tests --

    def test_list_endpoint_without_authentication_should_fail(self):
        response = self.client.get(self.list_endpoint)
        self.assertEqual(response.status_code, 401)

    def test_list_endpoint(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(self.list_endpoint)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.json()['count'], 2)

    def test_detail_endpoint_without_authentication_should_fail(self):
        response = self.client.get(self.detail_endpoint.format(pk=1))
        self.assertEqual(response.status_code, 401)

    def test_detail_endpoint(self):
        self.client.force_authenticate(user=self.superuser)

        pk = self.signal_no_image.id
        response = self.client.get(self.detail_endpoint.format(pk=pk))
        self.assertEqual(response.status_code, 200)

        # TODO: add more detailed tests using a JSONSchema
        # TODO: consider naming of 'note' object (is list, so 'notes')?
        response_json = response.json()
        for key in ['status', 'category', 'priority', 'location', 'reporter', 'notes', 'image']:
            self.assertIn(key, response_json)

    def test_history_action(self):
        self.client.force_authenticate(user=self.superuser)

        pk = self.signal_no_image.id
        response = self.client.get(self.history_endpoint.format(pk=pk))
        self.assertEqual(response.status_code, 200)

        # SIA currently does 4 updates before Signal is fully in the system
        self.assertEqual(len(response.json()), 4)

    def test_history_action_filters(self):
        self.client.force_authenticate(user=self.superuser)

        pk = self.signal_no_image.id
        base_url = self.history_endpoint.format(pk=pk)

        # TODO: elaborate filter testing in tests with interactions with API
        for filter_value, n_results in [
            ('UPDATE_STATUS', 1),
            ('UPDATE_LOCATION', 1),
            ('UPDATE_CATEGORY_ASSIGNMENT', 1),
            ('UPDATE_PRIORITY', 1),
        ]:
            querystring = urlencode({'what': filter_value})
            result = self.client.get(base_url + '?' + querystring)
            self.assertEqual(len(result.json()), n_results)

        # Filter by non-existing value, should get zero results
        querystring = urlencode({'what': 'DOES_NOT_EXIST'})
        result = self.client.get(base_url + '?' + querystring)
        self.assertEqual(len(result.json()), 0)

    # -- write tests --

    @patch("signals.apps.signals.address.validation.AddressValidation.validate_address_dict",
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_initial(self, validate_address_dict):
        # Authenticate, load fixture and add relevant main and sub category.
        self.client.force_authenticate(user=self.superuser)

        # Create initial Signal, check that it reached the database.
        signal_count = Signal.objects.count()
        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Signal.objects.count(), signal_count + 1)

        # Check that the actions are logged with the correct user email
        new_url = response.json()['_links']['self']['href']
        response_json = self.client.get(new_url).json()

        self.assertEqual(response_json['status']['user'], self.superuser.email)
        self.assertEqual(response_json['priority']['created_by'], self.superuser.email)
        self.assertEqual(response_json['location']['created_by'], self.superuser.email)
        self.assertEqual(response_json['category']['created_by'], self.superuser.email)

    @patch("signals.apps.signals.address.validation.AddressValidation.validate_address_dict",
           side_effect=NoResultsException)
    def test_create_initial_invalid_location(self, validate_address_dict):
        """ Tests that a 400 is returned when an invalid location is provided """

        self.client.force_authenticate(user=self.superuser)
        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')

        self.assertEqual(response.status_code, 400)

    @patch("signals.apps.signals.address.validation.AddressValidation.validate_address_dict")
    def test_create_initial_valid_location(self, validate_address_dict):
        """ Tests that bag_validated is set to True when a valid location is provided and that
        the address is replaced with the suggested address. The original address should be saved
        in the extra_properties of the Location object """

        original_address = self.create_initial_data["location"]["address"]
        suggested_address = self.create_initial_data["location"]["address"]
        suggested_address["openbare_ruimte"] = "Amsteltje"
        validate_address_dict.return_value = suggested_address

        self.client.force_authenticate(user=self.superuser)
        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')

        self.assertEqual(response.status_code, 201)

        signal_id = response.data['id']
        signal = Signal.objects.get(id=signal_id)

        self.assertTrue(signal.location.bag_validated)
        self.assertEquals(original_address, signal.location.extra_properties["original_address"],
                          "Original address should appear in extra_properties.original_address")
        self.assertEquals(suggested_address, signal.location.address,
                          "Suggested address should appear instead of the received address")

    @patch("signals.apps.signals.address.validation.AddressValidation.validate_address_dict",
           side_effect=AddressValidationUnavailableException)
    def test_create_initial_address_validation_unavailable(self, validate_address_dict):
        """ Tests that the signal is created even though the address validation service is
        unavailable. Should set bag_validated to False """

        self.client.force_authenticate(user=self.superuser)
        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')

        self.assertEqual(response.status_code, 201)

        signal_id = response.data['id']
        signal = Signal.objects.get(id=signal_id)

        # Signal should be added, but bag_validated should be False
        self.assertFalse(signal.location.bag_validated)

    @patch("signals.apps.signals.address.validation.AddressValidation.validate_address_dict",
           side_effect=AddressValidationUnavailableException)
    def test_create_initial_try_update_bag_validated(self, validate_address_dict):
        """ Tests that the bag_validated field cannot be set manually, and that the address
        validation is called """

        self.client.force_authenticate(user=self.superuser)

        data = self.create_initial_data
        data['location']['bag_validated'] = True
        response = self.client.post(self.list_endpoint, data, format='json')

        validate_address_dict.assert_called_once()

        self.assertEqual(response.status_code, 201)

        signal_id = response.data['id']
        signal = Signal.objects.get(id=signal_id)

        self.assertFalse(signal.location.bag_validated)

    @patch("signals.apps.signals.address.validation.AddressValidation.validate_address_dict",
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_initial_and_upload_image(self, validate_address_dict):
        # Authenticate, load fixture.
        self.client.force_authenticate(user=self.superuser)

        # Create initial Signal.
        signal_count = Signal.objects.count()
        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Signal.objects.count(), signal_count + 1)

        # Store URL of the newly created Signal, then upload image to it.
        new_url = response.json()['_links']['self']['href']

        new_image_url = f'{new_url}/image'
        image = SimpleUploadedFile('image.gif', self.small_gif, content_type='image/gif')
        response = self.client.post(new_image_url, data={'image': image})

        self.assertEqual(response.status_code, 202)

        # Check that a second upload is rejected
        response = self.client.post(new_image_url, data={'image': image})
        self.assertEqual(response.status_code, 403)

    @skip('Updates not yet supported')
    def test_update_location(self):
        # Partial update to update the location, all interaction via API.
        self.client.force_authenticate(user=self.superuser)

        pk = self.signal_no_image.id
        detail_endpoint = self.detail_endpoint.format(pk=pk)
        history_endpoint = self.history_endpoint.format(pk=pk)

        # check that only one Location is in the history
        querystring = urlencode({'what': 'UPDATE_LOCATION'})
        response = self.client.get(history_endpoint + '?' + querystring)
        self.assertEqual(len(response.json()), 1)

        # retrieve relevant fixture
        fixture_file = os.path.join(THIS_DIR, 'update_location.json')
        with open(fixture_file, 'r') as f:
            data = json.load(f)

        # update location, check that the correct user performed the action.
        response = self.client.patch(detail_endpoint, data, format='json')
        self.assertEqual(response.status_code, 200)

        # check that there are two Locations is in the history
        response = self.client.get(history_endpoint + '?' + querystring)
        self.assertEqual(len(response.json()), 2)

        self.signal_no_image.refresh_from_db()
        self.assertEqual(
            self.signal_no_image.location.created_by,
            self.superuser.email,
        )

    def test_update_status(self):
        # Partial update to update the status, all interaction via API.
        self.client.force_authenticate(user=self.superuser)

        pk = self.signal_no_image.id
        detail_endpoint = self.detail_endpoint.format(pk=pk)
        history_endpoint = self.history_endpoint.format(pk=pk)

        # check that only one Status is in the history
        querystring = urlencode({'what': 'UPDATE_STATUS'})
        response = self.client.get(history_endpoint + '?' + querystring)
        self.assertEqual(len(response.json()), 1)

        # retrieve relevant fixture
        fixture_file = os.path.join(THIS_DIR, 'update_status.json')
        with open(fixture_file, 'r') as f:
            data = json.load(f)

        response = self.client.patch(detail_endpoint, data, format='json')
        self.assertEqual(response.status_code, 200)

        # check that there are two Statusses is in the history
        self.signal_no_image.refresh_from_db()
        response = self.client.get(history_endpoint + '?' + querystring)
        self.assertEqual(len(response.json()), 2)

        # check that the correct user is logged
        self.signal_no_image.refresh_from_db()
        self.assertEqual(
            self.signal_no_image.status.user,
            self.superuser.email,
        )

    def test_update_category_assignment(self):
        # Partial update to update the location, all interaction via API.
        self.client.force_authenticate(user=self.superuser)

        pk = self.signal_no_image.id
        detail_endpoint = self.detail_endpoint.format(pk=pk)
        history_endpoint = self.history_endpoint.format(pk=pk)

        # check that only one category assignment is in the history
        querystring = urlencode({'what': 'UPDATE_CATEGORY_ASSIGNMENT'})
        response = self.client.get(history_endpoint + '?' + querystring)
        self.assertEqual(len(response.json()), 1)

        # retrieve relevant fixture
        fixture_file = os.path.join(THIS_DIR, 'update_category_assignment.json')
        with open(fixture_file, 'r') as f:
            data = json.load(f)
        data['category']['sub_category'] = self.link_test_cat_sub

        response = self.client.patch(detail_endpoint, data, format='json')
        self.assertEqual(response.status_code, 200)

        # check that there are two category assignments in the history
        self.signal_no_image.refresh_from_db()

        response = self.client.get(history_endpoint + '?' + querystring)
        self.assertEqual(len(response.json()), 2)

        # check that the correct user is logged
        self.signal_no_image.refresh_from_db()
        self.assertEqual(
            self.signal_no_image.category_assignment.created_by,
            self.superuser.email,
        )

    def test_update_priority(self):
        # Partial update to update the priority, all interaction via API.
        self.client.force_authenticate(user=self.superuser)

        pk = self.signal_no_image.id
        detail_endpoint = self.detail_endpoint.format(pk=pk)
        history_endpoint = self.history_endpoint.format(pk=pk)

        # check that only one Priority is in the history
        querystring = urlencode({'what': 'UPDATE_PRIORITY'})
        response = self.client.get(history_endpoint + '?' + querystring)
        self.assertEqual(len(response.json()), 1)

        # retrieve relevant fixture
        fixture_file = os.path.join(THIS_DIR, 'update_priority.json')
        with open(fixture_file, 'r') as f:
            data = json.load(f)

        response = self.client.patch(detail_endpoint, data, format='json')
        self.assertEqual(response.status_code, 200)

        # check that there are two priorities is in the history
        self.signal_no_image.refresh_from_db()
        response = self.client.get(history_endpoint + '?' + querystring)
        self.assertEqual(len(response.json()), 2)

        # check that the correct user is logged
        self.signal_no_image.refresh_from_db()
        self.assertEqual(
            self.signal_no_image.priority.created_by,
            self.superuser.email,
        )

    def test_create_note(self):
        # Partial update to update the status, all interaction via API.
        self.client.force_authenticate(user=self.superuser)

        pk = self.signal_no_image.id
        detail_endpoint = self.detail_endpoint.format(pk=pk)
        history_endpoint = self.history_endpoint.format(pk=pk)

        # check that there is no Note the history
        querystring = urlencode({'what': 'CREATE_NOTE'})
        response = self.client.get(history_endpoint + '?' + querystring)
        self.assertEqual(len(response.json()), 0)

        # retrieve relevant fixture
        fixture_file = os.path.join(THIS_DIR, 'create_note.json')
        with open(fixture_file, 'r') as f:
            data = json.load(f)

        response = self.client.patch(detail_endpoint, data, format='json')
        self.assertEqual(response.status_code, 200)

        # check that there is now one Note in the history
        self.signal_no_image.refresh_from_db()
        response = self.client.get(history_endpoint + '?' + querystring)
        self.assertEqual(len(response.json()), 1)

        # check that the correct user is logged
        self.signal_no_image.refresh_from_db()
        self.assertEqual(
            self.signal_no_image.notes.first().created_by,
            self.superuser.email,
        )

    def test_put_not_allowed(self):
        # Partial update to update the status, all interaction via API.
        self.client.force_authenticate(user=self.superuser)

        pk = self.signal_no_image.id
        detail_endpoint = self.detail_endpoint.format(pk=pk)

        response = self.client.put(detail_endpoint, {}, format='json')
        self.assertEqual(response.status_code, 405)

# TODO:
# * Add test to check that an uploaded signal can only be created in gemeld state via public
#   unauthenticated endpoint.
