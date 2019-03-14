import copy
import json
import os
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.http import urlencode
from rest_framework.reverse import reverse

from signals import API_VERSIONS
from signals.apps.signals import workflow
from signals.apps.signals.address.validation import (
    AddressValidationUnavailableException,
    NoResultsException
)
from signals.apps.signals.models import Attachment, Category, History, MainCategory, Signal
from signals.utils.version import get_version
from tests.apps.signals.attachment_helpers import (
    add_image_attachments,
    add_non_image_attachments,
    small_gif
)
from tests.apps.signals.factories import (
    CategoryFactory,
    MainCategoryFactory,
    NoteFactory,
    SignalFactory,
    SignalFactoryValidLocation,
    SignalFactoryWithImage
)
from tests.test import SIAReadWriteUserMixin, SignalsBaseApiTestCase

THIS_DIR = os.path.dirname(__file__)


class TestAPIRoot(SignalsBaseApiTestCase):

    def test_http_header_api_version(self):
        response = self.client.get('/signals/v1/')

        self.assertEqual(response['X-API-Version'], get_version(API_VERSIONS['v1']))


class TestCategoryTermsEndpoints(SignalsBaseApiTestCase):
    fixtures = ['categories.json', ]

    def setUp(self):
        self.list_categories_schema = self.load_json_schema(
            os.path.join(
                THIS_DIR,
                'json_schema',
                'get_signals_v1_public_terms_categories.json'
            )
        )
        self.retrieve_category_schema = self.load_json_schema(
            os.path.join(
                THIS_DIR,
                'json_schema',
                'get_signals_v1_public_terms_categories_{slug}.json'
            )
        )
        self.retrieve_sub_category_schema = self.load_json_schema(
            os.path.join(
                THIS_DIR,
                'json_schema',
                'get_signals_v1_public_terms_categories_{slug}_sub_categories_{sub_slug}.json'
            )
        )

        super(TestCategoryTermsEndpoints, self).setUp()

    def test_category_list(self):
        # Asserting that we've 9 `MainCategory` objects loaded from the json fixture.
        self.assertEqual(MainCategory.objects.count(), 9)

        url = '/signals/v1/public/terms/categories/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()

        # JSONSchema validation
        self.assertJsonSchema(self.list_categories_schema, data)

        self.assertEqual(len(data['results']), 9)

    def test_category_detail(self):
        # Asserting that we've 13 sub categories for our main category "Afval".
        main_category = MainCategoryFactory.create(name='Afval')
        self.assertEqual(main_category.categories.count(), 13)

        url = '/signals/v1/public/terms/categories/{slug}'.format(slug=main_category.slug)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()

        # JSONSchema validation
        self.assertJsonSchema(self.retrieve_category_schema, data)

        self.assertEqual(data['name'], 'Afval')
        self.assertEqual(len(data['sub_categories']), 13)

    def test_sub_category_detail(self):
        sub_category = CategoryFactory.create(name='Grofvuil', parent__name='Afval')

        url = '/signals/v1/public/terms/categories/{slug}/sub_categories/{sub_slug}'.format(
            slug=sub_category.parent.slug,
            sub_slug=sub_category.slug)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()

        # JSONSchema validation
        self.assertJsonSchema(self.retrieve_sub_category_schema, data)

        self.assertEqual(data['name'], 'Grofvuil')
        self.assertIn('is_active', data)


class TestPrivateEndpoints(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
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


class TestHistoryAction(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    def setUp(self):
        self.signal = SignalFactory.create()

        self.list_history_schema = self.load_json_schema(
            os.path.join(
                THIS_DIR,
                'json_schema',
                'get_signals_v1_private_signals_{pk}_history.json'
            )
        )

    def test_history_action_present(self):
        response = self.client.get(f'/signals/v1/private/signals/{self.signal.id}/history')
        self.assertEqual(response.status_code, 401)

        self.client.force_authenticate(user=self.sia_read_write_user)
        response = self.client.get(f'/signals/v1/private/signals/{self.signal.id}/history')
        self.assertEqual(response.status_code, 200)

        # JSONSchema validation
        data = response.json()
        self.assertJsonSchema(self.list_history_schema, data)

    def test_history_endpoint_rendering(self):
        history_entries = History.objects.filter(_signal__id=self.signal.pk)

        self.client.force_authenticate(user=self.sia_read_write_user)
        response = self.client.get(f'/signals/v1/private/signals/{self.signal.id}/history')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data), history_entries.count())

        # JSONSchema validation
        self.assertJsonSchema(self.list_history_schema, data)

    def test_history_entry_contents(self):
        keys = ['identifier', 'when', 'what', 'action', 'description', 'who', '_signal']

        self.client.force_authenticate(user=self.sia_read_write_user)
        response = self.client.get(f'/signals/v1/private/signals/{self.signal.id}/history')
        self.assertEqual(response.status_code, 200)

        # JSONSchema validation
        data = response.json()
        self.assertJsonSchema(self.list_history_schema, data)

        for entry in data:
            for k in keys:
                self.assertIn(k, entry)

    def test_update_shows_up(self):
        # Get a baseline for the Signal history
        self.client.force_authenticate(user=self.sia_read_write_user)
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

        # JSONSchema validation
        data = response.json()
        self.assertJsonSchema(self.list_history_schema, data)

        new_entry = data[0]  # most recent status should be first
        self.assertEqual(new_entry['who'], self.user.username)
        self.assertEqual(new_entry['description'], status.text)


class TestPrivateSignalViewSet(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    """
    Test basic properties of the V1 /signals/v1/private/signals endpoint.

    Note: we check both the list endpoint and associated detail endpoint.
    """

    def setUp(self):
        # initialize database with 2 Signals
        self.signal_no_image = SignalFactoryValidLocation.create()
        self.signal_with_image = SignalFactoryWithImage.create()

        # No URL reversing here, these endpoints are part of the spec (and thus
        # should not change).
        self.list_endpoint = '/signals/v1/private/signals/'
        self.detail_endpoint = '/signals/v1/private/signals/{pk}'
        self.history_endpoint = '/signals/v1/private/signals/{pk}/history'
        self.history_image = '/signals/v1/private/signals/{pk}/image'
        self.split_endpoint = '/signals/v1/private/signals/{pk}/split'

        # Create a special pair of sub and main categories for testing (insulate our tests
        # from future changes in categories).
        # TODO: add to factories.
        self.test_cat_main = MainCategory(name='testmain')
        self.test_cat_main.save()
        self.test_cat_sub = Category(
            parent=self.test_cat_main,
            name='testsub',
            handling=Category.HANDLING_A3DMC,
        )
        self.test_cat_sub.save()
        assert 'sub-category-' not in self.test_cat_sub.slug

        self.link_test_cat_sub = reverse(
            'v1:category-detail', kwargs={
                'slug': self.test_cat_main.slug,
                'sub_slug': self.test_cat_sub.slug,
            }
        )

        # Load fixture of initial data, augment with above test categories.
        fixture_file = os.path.join(THIS_DIR, 'create_initial.json')
        with open(fixture_file, 'r') as f:
            self.create_initial_data = json.load(f)
        self.create_initial_data['category'] = {'sub_category': self.link_test_cat_sub}

        self.list_signals_schema = self.load_json_schema(
            os.path.join(
                THIS_DIR,
                'json_schema',
                'get_signals_v1_private_signals.json')
        )
        self.retrieve_signal_schema = self.load_json_schema(
            os.path.join(
                THIS_DIR,
                'json_schema',
                'get_signals_v1_private_signals_{pk}.json'
            )
        )
        self.list_history_schema = self.load_json_schema(
            os.path.join(
                THIS_DIR,
                'json_schema',
                'get_signals_v1_private_signals_{pk}_history.json'
            )
        )
        self.post_split_schema = self.load_json_schema(
            os.path.join(
                THIS_DIR,
                'json_schema',
                'post_signals_v1_private_signals_{pk}_split.json'
            )
        )

    # -- Read tests --

    def test_list_endpoint_without_authentication_should_fail(self):
        response = self.client.get(self.list_endpoint)
        self.assertEqual(response.status_code, 401)

    def test_list_endpoint(self):
        self.client.force_authenticate(user=self.sia_read_write_user)
        response = self.client.get(self.list_endpoint)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.json()['count'], 2)

        # JSONSchema validation
        data = response.json()
        self.assertJsonSchema(self.list_signals_schema, data)

    def test_detail_endpoint_without_authentication_should_fail(self):
        response = self.client.get(self.detail_endpoint.format(pk=1))
        self.assertEqual(response.status_code, 401)

    def test_detail_endpoint(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        pk = self.signal_no_image.id
        response = self.client.get(self.detail_endpoint.format(pk=pk))
        self.assertEqual(response.status_code, 200)

        # JSONSchema validation
        data = response.json()
        self.assertJsonSchema(self.retrieve_signal_schema, data)

    def test_history_action(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        pk = self.signal_no_image.id
        response = self.client.get(self.history_endpoint.format(pk=pk))
        self.assertEqual(response.status_code, 200)

        # SIA currently does 4 updates before Signal is fully in the system
        self.assertEqual(len(response.json()), 4)

        # JSONSchema validation
        data = response.json()
        self.assertJsonSchema(self.list_history_schema, data)

    def test_history_action_filters(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

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

        # JSONSchema validation
        data = result.json()
        self.assertJsonSchema(self.list_history_schema, data)

    # -- write tests --

    @patch("signals.apps.signals.address.validation.AddressValidation.validate_address_dict",
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_initial(self, validate_address_dict):
        # Authenticate, load fixture and add relevant main and sub category.
        self.client.force_authenticate(user=self.sia_read_write_user)

        # Create initial Signal, check that it reached the database.
        signal_count = Signal.objects.count()
        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Signal.objects.count(), signal_count + 1)

        # Check that the actions are logged with the correct user email
        new_url = response.json()['_links']['self']['href']
        response_json = self.client.get(new_url).json()

        # JSONSchema validation
        self.assertJsonSchema(self.retrieve_signal_schema, response_json)

        self.assertEqual(response_json['status']['user'], self.sia_read_write_user.email)
        self.assertEqual(response_json['priority']['created_by'], self.sia_read_write_user.email)
        self.assertEqual(response_json['location']['created_by'], self.sia_read_write_user.email)
        self.assertEqual(response_json['category']['created_by'], self.sia_read_write_user.email)

    def test_create_with_status(self):
        """ Tests that an error is returned when we try to set the status """
        self.client.force_authenticate(user=self.sia_read_write_user)

        initial_data = self.create_initial_data.copy()
        initial_data["status"] = {
            "state": workflow.BEHANDELING,
            "text": "Invalid stuff happening here"
        }

        response = self.client.post(self.list_endpoint, initial_data, format='json')

        self.assertEqual(400, response.status_code)

    @patch("signals.apps.signals.address.validation.AddressValidation.validate_address_dict",
           side_effect=NoResultsException)
    def test_create_initial_invalid_location(self, validate_address_dict):
        """ Tests that a 400 is returned when an invalid location is provided """

        self.client.force_authenticate(user=self.sia_read_write_user)
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

        self.client.force_authenticate(user=self.sia_read_write_user)
        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')

        self.assertEqual(response.status_code, 201)

        data = response.json()
        signal_id = response.data['id']
        signal = Signal.objects.get(id=signal_id)

        self.assertTrue(signal.location.bag_validated)
        self.assertEqual(original_address, signal.location.extra_properties["original_address"],
                         "Original address should appear in extra_properties.original_address")
        self.assertEqual(suggested_address, signal.location.address,
                         "Suggested address should appear instead of the received address")

        # JSONSchema validation
        new_url = data['_links']['self']['href']
        response_json = self.client.get(new_url).json()
        self.assertJsonSchema(self.retrieve_signal_schema, response_json)

    @patch("signals.apps.signals.address.validation.AddressValidation.validate_address_dict")
    def test_create_initial_valid_location_but_no_address(self, validate_address_dict):
        """Tests that a Signal can be created when loccation has no known address but
        coordinates are known."""
        del self.create_initial_data["location"]["address"]

        self.client.force_authenticate(user=self.sia_read_write_user)
        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')

        self.assertEqual(response.status_code, 201)
        validate_address_dict.assert_not_called()

        signal_id = response.data['id']
        signal = Signal.objects.get(id=signal_id)

        self.assertEqual(signal.location.bag_validated, False)

        # JSONSchema validation
        data = response.json()
        new_url = data['_links']['self']['href']
        response_json = self.client.get(new_url).json()
        self.assertJsonSchema(self.retrieve_signal_schema, response_json)

    @patch("signals.apps.signals.address.validation.AddressValidation.validate_address_dict",
           side_effect=AddressValidationUnavailableException)
    def test_create_initial_address_validation_unavailable(self, validate_address_dict):
        """ Tests that the signal is created even though the address validation service is
        unavailable. Should set bag_validated to False """

        self.client.force_authenticate(user=self.sia_read_write_user)
        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')

        self.assertEqual(response.status_code, 201)

        signal_id = response.data['id']
        signal = Signal.objects.get(id=signal_id)

        # Signal should be added, but bag_validated should be False
        self.assertFalse(signal.location.bag_validated)

        # JSONSchema validation
        data = response.json()
        new_url = data['_links']['self']['href']
        response_json = self.client.get(new_url).json()
        self.assertJsonSchema(self.retrieve_signal_schema, response_json)

    @patch("signals.apps.signals.address.validation.AddressValidation.validate_address_dict",
           side_effect=AddressValidationUnavailableException)
    def test_create_initial_try_update_bag_validated(self, validate_address_dict):
        """ Tests that the bag_validated field cannot be set manually, and that the address
        validation is called """

        self.client.force_authenticate(user=self.sia_read_write_user)

        data = self.create_initial_data
        data['location']['bag_validated'] = True
        response = self.client.post(self.list_endpoint, data, format='json')

        validate_address_dict.assert_called_once()

        self.assertEqual(response.status_code, 201)

        signal_id = response.data['id']
        signal = Signal.objects.get(id=signal_id)

        self.assertFalse(signal.location.bag_validated)

        # JSONSchema validation
        data = response.json()
        new_url = data['_links']['self']['href']
        response_json = self.client.get(new_url).json()
        self.assertJsonSchema(self.retrieve_signal_schema, response_json)

    @patch("signals.apps.signals.address.validation.AddressValidation.validate_address_dict",
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_initial_and_upload_image(self, validate_address_dict):
        # Authenticate, load fixture.
        self.client.force_authenticate(user=self.sia_read_write_user)

        # Create initial Signal.
        signal_count = Signal.objects.count()
        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Signal.objects.count(), signal_count + 1)

        # Store URL of the newly created Signal, then upload image to it.
        new_url = response.json()['_links']['self']['href']

        new_image_url = f'{new_url}/attachments'
        image = SimpleUploadedFile('image.gif', small_gif, content_type='image/gif')
        response = self.client.post(new_image_url, data={'file': image})

        self.assertEqual(response.status_code, 201)

        # Check that a second upload is NOT rejected
        image2 = SimpleUploadedFile('image.gif', small_gif, content_type='image/gif')
        response = self.client.post(new_image_url, data={'file': image2})
        self.assertEqual(response.status_code, 201)

        # JSONSchema validation
        response_json = self.client.get(new_url).json()
        self.assertJsonSchema(self.retrieve_signal_schema, response_json)

    @patch("signals.apps.signals.address.validation.AddressValidation.validate_address_dict")
    def test_update_location(self, validate_address_dict):
        # Partial update to update the location, all interaction via API.
        self.client.force_authenticate(user=self.sia_read_write_user)

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
        validated_address = copy.deepcopy(data['location']['address'])
        validate_address_dict.return_value = validated_address

        # update location
        response = self.client.patch(detail_endpoint, data, format='json')
        self.assertEqual(response.status_code, 200)

        # check that there are two Locations is in the history
        response = self.client.get(history_endpoint + '?' + querystring)
        self.assertEqual(len(response.json()), 2)

        self.signal_no_image.refresh_from_db()
        # Check that the correct user performed the action.
        self.assertEqual(
            self.signal_no_image.location.created_by,
            self.sia_read_write_user.email,
        )

        # JSONSchema validation
        response_json = response.json()
        self.assertJsonSchema(self.list_history_schema, response_json)

    @patch("signals.apps.signals.address.validation.AddressValidation.validate_address_dict")
    def test_update_location_no_address(self, validate_address_dict):
        # Partial update to update the location, all interaction via API.
        # SIA must also allow location updates without known address but with
        # known coordinates.
        self.client.force_authenticate(user=self.sia_read_write_user)

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
        del data['location']['address']

        # update location
        response = self.client.patch(detail_endpoint, data, format='json')
        self.assertEqual(response.status_code, 200)
        validate_address_dict.assert_not_called()

        # check that there are two Locations is in the history
        response = self.client.get(history_endpoint + '?' + querystring)
        self.assertEqual(len(response.json()), 2)

        self.signal_no_image.refresh_from_db()
        # Check that the correct user performed the action.
        self.assertEqual(
            self.signal_no_image.location.created_by,
            self.sia_read_write_user.email,
        )

        # JSONSchema validation
        response_json = response.json()
        self.assertJsonSchema(self.list_history_schema, response_json)

    @patch("signals.apps.signals.address.validation.AddressValidation.validate_address_dict")
    def test_update_location_no_coordinates(self, validate_address_dict):
        # Partial update to update the location, all interaction via API.
        # SIA must also allow location updates without known address but with
        # known coordinates.
        self.client.force_authenticate(user=self.sia_read_write_user)

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
        del data['location']['geometrie']

        # update location
        response = self.client.patch(detail_endpoint, data, format='json')
        self.assertEqual(response.status_code, 400)
        validate_address_dict.assert_not_called()

    def test_update_status(self):
        # Partial update to update the status, all interaction via API.
        self.client.force_authenticate(user=self.sia_read_write_user)

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
            self.sia_read_write_user.email,
        )

        # JSONSchema validation
        response_json = response.json()
        self.assertJsonSchema(self.list_history_schema, response_json)

    def test_update_status_signal_has_no_status(self):
        # A signal that has no status
        signal_no_status = SignalFactoryValidLocation.create(status=None)

        # Partial update to update the status, all interaction via API.
        self.client.force_authenticate(user=self.sia_read_write_user)

        detail_endpoint = self.detail_endpoint.format(pk=signal_no_status.id)
        history_endpoint = '?'.join([
            self.history_endpoint.format(pk=signal_no_status.id),
            urlencode({'what': 'UPDATE_STATUS'})
        ])

        # check that there is no Status is in the history
        response = self.client.get(history_endpoint)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

        # The only status that is allowed is "GEMELD" so let's set it
        data = {'status': {'text': 'Test status update', 'state': 'm'}}
        response = self.client.patch(detail_endpoint, data, format='json')
        self.assertEqual(response.status_code, 200)

        # check that the Status is there
        response = self.client.get(history_endpoint)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

        # check that the correct user is logged
        signal_no_status.refresh_from_db()
        self.assertEqual(signal_no_status.status.user, self.sia_read_write_user.email)

        # JSONSchema validation
        response_json = response.json()
        self.assertJsonSchema(self.list_history_schema, response_json)

    def test_update_status_signal_has_no_status_invalid_new_state(self):
        # A signal that has no status
        signal_no_status = SignalFactoryValidLocation.create(status=None)

        # Partial update to update the status, all interaction via API.
        self.client.force_authenticate(user=self.sia_read_write_user)

        detail_endpoint = self.detail_endpoint.format(pk=signal_no_status.id)
        history_endpoint = '?'.join([
            self.history_endpoint.format(pk=signal_no_status.id),
            urlencode({'what': 'UPDATE_STATUS'})
        ])

        # check that there is no Status is in the history
        response = self.client.get(history_endpoint)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

        # The only status that is allowed is "GEMELD" so check with a diferrent state
        data = {'status': {'text': 'Test status update', 'state': 'b'}}
        with self.assertRaises(ValidationError):
            self.client.patch(detail_endpoint, data, format='json')

        # check that the Status is there
        response = self.client.get(history_endpoint)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

        # JSONSchema validation
        response_json = response.json()
        self.assertJsonSchema(self.list_history_schema, response_json)

    def test_update_category_assignment(self):
        # Partial update to update the location, all interaction via API.
        self.client.force_authenticate(user=self.sia_read_write_user)

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
            self.sia_read_write_user.email,
        )

        # JSONSchema validation
        response_json = response.json()
        self.assertJsonSchema(self.list_history_schema, response_json)

    def test_update_category_assignment_same_category(self):
        self.client.force_authenticate(user=self.sia_read_write_user)
        pk = self.signal_no_image.id
        detail_endpoint = self.detail_endpoint.format(pk=pk)

        # retrieve relevant fixture
        fixture_file = os.path.join(THIS_DIR, 'update_category_assignment.json')
        with open(fixture_file, 'r') as f:
            data = json.load(f)
        data['category']['sub_category'] = self.link_test_cat_sub

        Signal.actions.update_category_assignment({'sub_category': self.test_cat_sub},
                                                  self.signal_no_image)
        self.signal_no_image.refresh_from_db()

        # Signal is initialised with a known category.
        cat_assignments_cnt = self.signal_no_image.category_assignments.count()

        # Update signal with same category
        response = self.client.patch(detail_endpoint, data, format='json')
        self.assertEqual(response.status_code, 200)

        # No category assignment should be added
        self.assertEquals(cat_assignments_cnt, self.signal_no_image.category_assignments.count())

    def test_update_priority(self):
        # Partial update to update the priority, all interaction via API.
        self.client.force_authenticate(user=self.sia_read_write_user)

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
            self.sia_read_write_user.email,
        )

        # JSONSchema validation
        response_json = response.json()
        self.assertJsonSchema(self.list_history_schema, response_json)

    def test_create_note(self):
        # Partial update to update the status, all interaction via API.
        self.client.force_authenticate(user=self.sia_read_write_user)

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
            self.sia_read_write_user.email,
        )

        # JSONSchema validation
        response_json = response.json()
        self.assertJsonSchema(self.list_history_schema, response_json)

    def test_put_not_allowed(self):
        # Partial update to update the status, all interaction via API.
        self.client.force_authenticate(user=self.sia_read_write_user)

        pk = self.signal_no_image.id
        detail_endpoint = self.detail_endpoint.format(pk=pk)

        response = self.client.put(detail_endpoint, {}, format='json')
        self.assertEqual(response.status_code, 405)

    def test_split(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        self.assertEqual(Signal.objects.count(), 2)

        pk = self.signal_no_image.id

        response = self.client.post(
            self.split_endpoint.format(pk=pk),
            [
                {
                    'text': 'Child #1',
                    'category': {'sub_category': self.link_test_cat_sub}
                },
                {
                    'text': 'Child #2',
                    'category': {'sub_category': self.link_test_cat_sub}
                }
            ],
            format='json'
        )

        self.assertEqual(response.status_code, 201)

        data = response.json()
        self.assertEqual(len(data['children']), 2)
        self.assertJsonSchema(self.post_split_schema, data)

        for item in data['children']:
            self.assertEqual(Signal.objects.count(), 4)

            response = self.client.get(self.detail_endpoint.format(pk=item['id']))
            self.assertEqual(response.status_code, 200)

            # TODO: add more detailed tests using a JSONSchema
            # TODO: consider naming of 'note' object (is list, so 'notes')?
            response_json = response.json()
            for key in ['status', 'category', 'priority', 'location', 'reporter', 'notes', 'image']:
                self.assertIn(key, response_json)

        self.assertEqual(4, Signal.objects.count())
        self.assertEqual(2, len(self.signal_no_image.children.all()))

    def test_split_children_must_inherit_these_properties(self):
        """When a signal is split its children must inherit certain properties."""

        def is_same_location(a, b):
            """Compare relevant parts of a Location object."""
            # TODO: consider moving to method on model.
            compare_keys = ['address_text', 'address', 'geometrie']

            if type(a) != type(b):
                return False

            for k in compare_keys:
                if a[k] != b[k]:
                    return False

            return True

        # Split the signal, take note of the returned children
        self.client.force_authenticate(user=self.sia_read_write_user)
        response = self.client.post(
            self.split_endpoint.format(pk=self.signal_no_image.id),
            [
                {
                    'text': 'Child #1',
                    'category': {'sub_category': self.link_test_cat_sub}
                },
                {
                    'text': 'Child #2',
                    'category': {'sub_category': self.link_test_cat_sub}
                }
            ],
            format='json'
        )

        self.assertEqual(response.status_code, 201)
        split_json = response.json()

        # Retrieve parent data
        response = self.client.get(self.detail_endpoint.format(pk=self.signal_no_image.id))
        parent_json = response.json()

        for item in split_json['children']:
            # Retrieve detailed data on each child:
            response = self.client.get(self.detail_endpoint.format(pk=item['id']))
            child_json = response.json()

            # Check that status is correctly set
            self.assertIsNotNone(child_json['status'])
            self.assertEqual(child_json['status']['state'], workflow.GEMELD)

            # Check that the location is correctly set
            self.assertIsNotNone(child_json['location'])
            self.assertTrue(is_same_location(parent_json['location'], child_json['location']))

            # Check that the reporter is correctly set
            self.assertIsNotNone(child_json['reporter'])
            self.assertEqual(child_json['reporter']['email'], parent_json['reporter']['email'])

            # Check that the priority is correctly set
            self.assertIsNotNone(child_json['priority'])
            self.assertEqual(
                child_json['priority']['priority'],
                parent_json['priority']['priority']
            )

            # Check category assignment
            self.assertEqual(
                child_json['category']['sub_slug'],
                self.test_cat_sub.slug
            )
            self.assertEqual(
                child_json['category']['main_slug'],
                self.test_cat_main.slug
            )

    def test_split_children_must_inherit_parent_images(self):
        # Split the signal, take note of the returned children

        def md5(fname):
            import hashlib
            hash_md5 = hashlib.md5()
            with open(fname, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()

        self.client.force_authenticate(user=self.sia_read_write_user)
        response = self.client.post(
            self.split_endpoint.format(pk=self.signal_with_image.id),
            [
                {
                    'text': 'Child #1',
                    'reuse_parent_image': True,
                    'category': {'sub_category': self.link_test_cat_sub}
                },
                {
                    'text': 'Child #2',
                    'reuse_parent_image': True,
                    'category': {'sub_category': self.link_test_cat_sub}
                }
            ],
            format='json'
        )
        self.assertEqual(response.status_code, 201)

        self.signal_with_image.refresh_from_db()

        md5_parent_image = md5(self.signal_with_image.image.path)
        for child_signal in self.signal_with_image.children.all():
            md5_child_image = md5(child_signal.image.path)

            self.assertEqual(md5_parent_image, md5_child_image)

    def test_split_children_must_inherit_parent_images_for_1st_child(self):
        # Split the signal, take note of the returned children

        self.client.force_authenticate(user=self.sia_read_write_user)
        response = self.client.post(
            self.split_endpoint.format(pk=self.signal_with_image.id),
            [
                {
                    'text': 'Child #1',
                    'reuse_parent_image': True,
                    'category': {'sub_category': self.link_test_cat_sub}
                },
                {
                    'text': 'Child #2',
                    'category': {'sub_category': self.link_test_cat_sub}
                }
            ],
            format='json'
        )
        self.assertEqual(response.status_code, 201)

        self.signal_with_image.refresh_from_db()

        child_signal_1 = self.signal_with_image.children.first()
        self.assertNotEqual(child_signal_1.image, '')

        child_signal_2 = self.signal_with_image.children.last()
        self.assertEqual(child_signal_2.image, '')

    def _create_split_signal(self):
        parent_signal = SignalFactory.create()
        split_data = [
            {
                "text": "Child signal 1",
                'category': {'sub_category': self.test_cat_sub}
            },
            {
                "text": "Child signal 2",
                'category': {'sub_category': self.test_cat_sub}
            }
        ]
        Signal.actions.split(split_data, parent_signal)

        return parent_signal

    def test_split_get_split_signal(self):
        """ A GET /<signal_id>/split on a split signal should return a 200 with its
        children in the response body """

        signal = self._create_split_signal()
        self.client.force_authenticate(user=self.sia_read_write_user)
        response = self.client.get(self.split_endpoint.format(pk=signal.pk))

        self.assertEqual(200, response.status_code)
        json_response = response.json()

        self.assertEqual(2, len(json_response['children']))
        self.assertEqual("Child signal 1", json_response['children'][0]['text'])
        self.assertEqual("Child signal 2", json_response['children'][1]['text'])

        self.assertJsonSchema(self.post_split_schema, json_response)

    def test_split_get_not_split_signal(self):
        """ A GET /<signal_id>/split on a non-split signal should return a 404 """

        signal = SignalFactory.create()
        self.client.force_authenticate(user=self.sia_read_write_user)
        response = self.client.get(self.split_endpoint.format(pk=signal.pk))
        self.assertEqual(404, response.status_code)

    def test_split_post_split_signal(self):
        """ A POST /<signal_id>/split on an already updated signal should return a 412 """

        signal = self._create_split_signal()
        data = [{"text": "Child 1"}, {"text": "Child 2"}]
        self.client.force_authenticate(user=self.sia_read_write_user)
        response = self.client.post(self.split_endpoint.format(pk=signal.pk), data, format='json')
        self.assertEqual(412, response.status_code)
        self.assertEqual("Signal has already been split", response.json()["detail"])

    def test_child_cannot_be_split(self):
        """Child signals cannot themselves have children (i.e. not be split)."""
        self.client.force_authenticate(user=self.sia_read_write_user)
        pk = self.signal_no_image.id

        response = self.client.post(
            self.split_endpoint.format(pk=pk),
            [
                {
                    'text': 'Child #1',
                    'category': {'sub_category': self.link_test_cat_sub}
                },
                {
                    'text': 'Child #2',
                    'category': {'sub_category': self.link_test_cat_sub}
                }
            ],
            format='json'
        )

        self.assertEqual(response.status_code, 201)

        data = response.json()
        self.assertEqual(len(data['children']), 2)
        self.assertJsonSchema(self.post_split_schema, data)

        # Try to split each of the children, should produce HTTP 412 pre-
        # condition failed.
        for item in data['children']:
            pk = item['id']
            response = self.client.post(
                self.split_endpoint.format(pk=item['id']),
                [
                    {
                        'text': 'Child #1',
                        'category': {'sub_category': self.link_test_cat_sub}
                    },
                    {
                        'text': 'Child #2',
                        'category': {'sub_category': self.link_test_cat_sub}
                    }
                ],
                format='json',
            )
            self.assertEqual(response.status_code, 412)

    def test_split_empty_data(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        self.assertEqual(Signal.objects.count(), 2)

        pk = self.signal_no_image.id

        response = self.client.post(
            self.split_endpoint.format(pk=pk),
            None,
            format='json'
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()['children'],
            "A signal can only be split into min 2 and max 3 signals"
        )

        self.assertEqual(Signal.objects.count(), 2)

    def test_split_less_than_min_data(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        self.assertEqual(Signal.objects.count(), 2)

        pk = self.signal_no_image.id

        response = self.client.post(
            self.split_endpoint.format(pk=pk),
            [
                {
                    'text': 'Child #1',
                    'category': {'sub_category': self.link_test_cat_sub}
                },
            ],
            format='json'
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()['children'],
            'A signal can only be split into min 2 and max 3 signals'
        )

        self.assertEqual(Signal.objects.count(), 2)

    def test_split_more_than_max_data(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        self.assertEqual(Signal.objects.count(), 2)

        pk = self.signal_no_image.id

        response = self.client.post(
            self.split_endpoint.format(pk=pk),
            [
                {
                    'text': 'Child #1',
                    'category': {'sub_category': self.link_test_cat_sub}
                },
                {
                    'text': 'Child #2',
                    'category': {'sub_category': self.link_test_cat_sub}
                },
                {
                    'text': 'Child #3',
                    'category': {'sub_category': self.link_test_cat_sub}
                },
                {
                    'text': 'Child #4',
                    'category': {'sub_category': self.link_test_cat_sub}
                },
            ],
            format='json'
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()['children'],
            'A signal can only be split into min 2 and max 3 signals'
        )

        self.assertEqual(Signal.objects.count(), 2)


class TestPrivateSignalAttachments(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    list_endpoint = '/signals/v1/private/signals/'
    detail_endpoint = list_endpoint + '{}/'
    attachment_endpoint = detail_endpoint + 'attachments'
    test_host = 'http://testserver'

    def setUp(self):
        self.signal = SignalFactory.create()
        self.client.force_authenticate(user=self.sia_read_write_user)

        fixture_file = os.path.join(THIS_DIR, 'create_initial.json')

        with open(fixture_file, 'r') as f:
            self.create_initial_data = json.load(f)

        self.subcategory = CategoryFactory.create()

        link_test_cat_sub = reverse(
            'v1:category-detail', kwargs={
                'slug': self.subcategory.parent.slug,
                'sub_slug': self.subcategory.slug,
            }
        )

        self.create_initial_data['category'] = {'sub_category': link_test_cat_sub}

    def test_image_upload(self):
        endpoint = self.attachment_endpoint.format(self.signal.id)
        image = SimpleUploadedFile('image.gif', small_gif, content_type='image/gif')

        response = self.client.post(endpoint, data={'file': image})

        self.assertEqual(response.status_code, 201)
        self.assertIsInstance(self.signal.attachments.first(), Attachment)
        self.assertIsInstance(self.signal.attachments.filter(is_image=True).first(), Attachment)

    def test_attachment_upload(self):
        endpoint = self.attachment_endpoint.format(self.signal.id)
        doc_upload = os.path.join(THIS_DIR, 'sia-ontwerp-testfile.doc')

        with open(doc_upload, encoding='latin-1') as f:
            data = {"file": f}

            response = self.client.post(endpoint, data)

        self.assertEqual(response.status_code, 201)
        self.assertIsInstance(self.signal.attachments.first(), Attachment)
        self.assertIsNone(self.signal.attachments.filter(is_image=True).first())
        self.assertEqual(self.sia_read_write_user.email, self.signal.attachments.first().created_by)

    def test_create_contains_image_and_attachments(self):
        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertTrue('image' in response.json())
        self.assertTrue('attachments' in response.json())
        self.assertIsInstance(response.json()['attachments'], list)

    def test_get_detail_contains_image_and_attachments(self):
        non_image_attachments = add_non_image_attachments(self.signal, 1)
        image_attachments = add_image_attachments(self.signal, 2)
        non_image_attachments += add_non_image_attachments(self.signal, 1)

        response = self.client.get(self.list_endpoint, self.create_initial_data)
        self.assertEqual(200, response.status_code)

        json_item = response.json()['results'][0]
        self.assertTrue('image' in json_item)
        self.assertTrue('attachments' in json_item)
        self.assertEqual(self.test_host + image_attachments[0].file.url, json_item['image'])
        self.assertEqual(4, len(json_item['attachments']))
        self.assertEqual(self.test_host + image_attachments[0].file.url,
                         json_item['attachments'][1]['file'])
        self.assertTrue(json_item['attachments'][2]['is_image'])
        self.assertEqual(self.test_host + non_image_attachments[1].file.url,
                         json_item['attachments'][3]['file'])
        self.assertFalse(json_item['attachments'][3]['is_image'])

    def test_get_list_contains_image_and_attachments(self):
        non_image_attachments = add_non_image_attachments(self.signal, 1)
        image_attachments = add_image_attachments(self.signal, 2)
        non_image_attachments += add_non_image_attachments(self.signal, 1)

        response = self.client.get(self.list_endpoint, self.create_initial_data)
        self.assertEqual(200, response.status_code)

        json_item = response.json()['results'][0]
        self.assertTrue('image' in json_item)
        self.assertTrue('attachments' in json_item)
        self.assertEqual(self.test_host + image_attachments[0].file.url, json_item['image'])
        self.assertEqual(4, len(json_item['attachments']))
        self.assertEqual(self.test_host + image_attachments[0].file.url,
                         json_item['attachments'][1]['file'])
        self.assertTrue(json_item['attachments'][2]['is_image'])
        self.assertEqual(self.test_host + non_image_attachments[1].file.url,
                         json_item['attachments'][3]['file'])
        self.assertFalse(json_item['attachments'][3]['is_image'])


class TestPublicSignalViewSet(SignalsBaseApiTestCase):
    list_endpoint = "/signals/v1/public/signals/"
    detail_endpoint = list_endpoint + "{uuid}"
    attachment_endpoint = detail_endpoint + "/attachments"

    fixture_file = os.path.join(THIS_DIR, 'create_initial.json')

    def setUp(self):
        with open(self.fixture_file, 'r') as f:
            self.create_initial_data = json.load(f)

        self.subcategory = CategoryFactory.create()

        link_test_cat_sub = reverse(
            'v1:category-detail', kwargs={
                'slug': self.subcategory.parent.slug,
                'sub_slug': self.subcategory.slug,
            }
        )

        self.create_initial_data['category'] = {'sub_category': link_test_cat_sub}

        self.retrieve_schema = self.load_json_schema(
            os.path.join(
                THIS_DIR,
                'json_schema',
                'get_signals_v1_public_signals_{uuid}.json'
            )
        )
        self.create_schema = self.load_json_schema(
            os.path.join(
                THIS_DIR,
                'json_schema',
                'post_signals_v1_public_signals.json'
            )
        )
        self.create_attachment_schema = self.load_json_schema(
            os.path.join(
                THIS_DIR,
                'json_schema',
                'post_signals_v1_public_signals_attachment.json'
            )
        )

    def test_create(self):
        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')

        self.assertEqual(201, response.status_code)
        self.assertJsonSchema(self.create_schema, response.json())
        self.assertEqual(1, Signal.objects.count())
        self.assertTrue('image' in response.json())
        self.assertTrue('attachments' in response.json())
        self.assertIsInstance(response.json()['attachments'], list)

        signal = Signal.objects.last()
        self.assertEqual(workflow.GEMELD, signal.status.state)
        self.assertEqual(self.subcategory, signal.category_assignment.category)
        self.assertEqual("melder@example.com", signal.reporter.email)
        self.assertEqual("Amstel 1 1011PN Amsterdam", signal.location.address_text)
        self.assertEqual("Luidruchtige vergadering", signal.text)
        self.assertEqual("extra: heel luidruchtig debat", signal.text_extra)

    def test_create_with_status(self):
        """ Tests that an error is returned when we try to set the status """

        initial_data = self.create_initial_data.copy()
        initial_data["status"] = {
            "state": workflow.BEHANDELING,
            "text": "Invalid stuff happening here"
        }

        response = self.client.post(self.list_endpoint, initial_data, format='json')

        self.assertEqual(400, response.status_code)
        self.assertEqual(0, Signal.objects.count())

    def test_get_by_uuid(self):
        signal = SignalFactory.create()
        uuid = signal.signal_id

        response = self.client.get(self.detail_endpoint.format(uuid=uuid), format='json')

        self.assertEqual(200, response.status_code)
        self.assertJsonSchema(self.retrieve_schema, response.json())

    def test_add_attachment_imagetype(self):
        signal = SignalFactory.create()
        uuid = signal.signal_id

        data = {"file": SimpleUploadedFile('image.gif', small_gif, content_type='image/gif')}

        response = self.client.post(self.attachment_endpoint.format(uuid=uuid), data)

        self.assertEqual(201, response.status_code)
        self.assertJsonSchema(self.create_attachment_schema, response.json())

        attachment = Attachment.objects.last()
        self.assertEqual("image/gif", attachment.mimetype)
        self.assertIsInstance(attachment.image_crop.url, str)
        self.assertIsNone(attachment.created_by)

    def test_add_attachment_nonimagetype(self):
        signal = SignalFactory.create()
        uuid = signal.signal_id

        doc_upload = os.path.join(THIS_DIR, 'sia-ontwerp-testfile.doc')
        with open(doc_upload, encoding='latin-1') as f:
            data = {"file": f}

            response = self.client.post(self.attachment_endpoint.format(uuid=uuid), data)

        self.assertEqual(201, response.status_code)
        self.assertJsonSchema(self.create_attachment_schema, response.json())

        attachment = Attachment.objects.last()
        self.assertEqual("application/msword", attachment.mimetype)
