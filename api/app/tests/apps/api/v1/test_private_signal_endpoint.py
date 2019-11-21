import copy
import json
import os
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone
from django.utils.http import urlencode
from freezegun import freeze_time
from rest_framework import status

from signals.apps.api.v1.validation import AddressValidationUnavailableException, NoResultsException
from signals.apps.signals import workflow
from signals.apps.signals.models import Attachment, Signal
from tests.apps.signals.attachment_helpers import (
    add_image_attachments,
    add_non_image_attachments,
    small_gif
)
from tests.apps.signals.factories import (
    CategoryFactory,
    DepartmentFactory,
    ParentCategoryFactory,
    SignalFactory,
    SignalFactoryValidLocation,
    SignalFactoryWithImage
)
from tests.apps.users.factories import GroupFactory
from tests.test import SIAReadWriteUserMixin, SignalsBaseApiTestCase

THIS_DIR = os.path.dirname(__file__)
SIGNALS_TEST_DIR = os.path.join(os.path.split(THIS_DIR)[0], '..', 'signals')


class TestPrivateSignalEndpointUnAuthorized(SignalsBaseApiTestCase):
    def test_list_endpoint(self):
        response = self.client.get('/signals/v1/private/signals/')
        self.assertEqual(response.status_code, 401)

    def test_detail_endpoint(self):
        response = self.client.get('/signals/v1/private/signals/1')
        self.assertEqual(response.status_code, 401)

    def test_create_endpoint(self):
        response = self.client.post('/signals/v1/private/signals/1', {})
        self.assertEqual(response.status_code, 401)

    def test_update_endpoint(self):
        response = self.client.put('/signals/v1/private/signals/1', {})
        self.assertEqual(response.status_code, 401)

        response = self.client.patch('/signals/v1/private/signals/1', {})
        self.assertEqual(response.status_code, 401)

    def test_delete_endpoint(self):
        response = self.client.delete('/signals/v1/private/signals/1')
        self.assertEqual(response.status_code, 401)


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
        self.removed_from_category_endpoint = '/signals/v1/private/signals/category/removed'

        self.subcategory = CategoryFactory.create()
        self.link_subcategory = '/signals/v1/public/terms/categories/{}/sub_categories/{}'.format(
            self.subcategory.parent.slug, self.subcategory.slug
        )

        # Load fixture of initial data, augment with above test categories.
        fixture_file = os.path.join(THIS_DIR, 'request_data', 'create_initial.json')
        with open(fixture_file, 'r') as f:
            self.create_initial_data = json.load(f)

        # Add a generated category
        self.create_initial_data['source'] = 'valid-source'
        self.create_initial_data['category'] = {'category_url': self.link_subcategory}

        self.list_signals_schema = self.load_json_schema(
            os.path.join(THIS_DIR, 'json_schema', 'get_signals_v1_private_signals.json')
        )
        self.retrieve_signal_schema = self.load_json_schema(
            os.path.join(THIS_DIR, 'json_schema', 'get_signals_v1_private_signals_{pk}.json')
        )
        self.list_history_schema = self.load_json_schema(
            os.path.join(THIS_DIR, 'json_schema', 'get_signals_v1_private_signals_{pk}_history.json')  # noqa
        )
        self.post_split_schema = self.load_json_schema(
            os.path.join(THIS_DIR, 'json_schema', 'post_signals_v1_private_signals_{pk}_split.json')
        )
        self.client.force_authenticate(user=self.sia_read_write_user)

    # -- Read tests --
    def test_list_endpoint(self):
        response = self.client.get(self.list_endpoint)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.json()['count'], 2)

        # JSONSchema validation
        data = response.json()
        self.assertJsonSchema(self.list_signals_schema, data)

    def test_detail_endpoint(self):
        response = self.client.get(self.detail_endpoint.format(pk=self.signal_no_image.id))
        self.assertEqual(response.status_code, 200)

        # JSONSchema validation
        data = response.json()
        self.assertJsonSchema(self.retrieve_signal_schema, data)

    def test_history_action(self):
        response = self.client.get(self.history_endpoint.format(pk=self.signal_no_image.id))
        self.assertEqual(response.status_code, 200)

        # SIA currently does 4 updates before Signal is fully in the system
        self.assertEqual(len(response.json()), 4)

        # JSONSchema validation
        data = response.json()
        self.assertJsonSchema(self.list_history_schema, data)

    def test_history_action_filters(self):
        base_url = self.history_endpoint.format(pk=self.signal_no_image.id)

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

    @patch("signals.apps.api.v1.validation.AddressValidation.validate_address_dict",
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_initial(self, validate_address_dict):
        # Create initial Signal, check that it reached the database.
        signal_count = Signal.objects.count()
        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Signal.objects.count(), signal_count + 1)

        # Check that the actions are logged with the correct user email
        new_url = response.json()['_links']['self']['href']
        response = self.client.get(new_url)
        response_json = response.json()

        # JSONSchema validation
        self.assertJsonSchema(self.retrieve_signal_schema, response_json)

        self.assertEqual(response_json['status']['user'], self.sia_read_write_user.email)
        self.assertEqual(response_json['priority']['created_by'], self.sia_read_write_user.email)
        self.assertEqual(response_json['location']['created_by'], self.sia_read_write_user.email)
        self.assertEqual(response_json['category']['created_by'], self.sia_read_write_user.email)

    def test_create_with_status(self):
        """ Tests that an error is returned when we try to set the status """
        initial_data = self.create_initial_data.copy()
        initial_data["status"] = {
            "state": workflow.BEHANDELING,
            "text": "Invalid stuff happening here"
        }

        response = self.client.post(self.list_endpoint, initial_data, format='json')

        self.assertEqual(400, response.status_code)

    @patch("signals.apps.api.v1.validation.AddressValidation.validate_address_dict",
           side_effect=NoResultsException)
    def test_create_initial_invalid_location(self, validate_address_dict):
        """ Tests that a 400 is returned when an invalid location is provided """
        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')

        self.assertEqual(response.status_code, 400)

    @patch("signals.apps.api.v1.validation.AddressValidation.validate_address_dict")
    def test_create_initial_valid_location(self, validate_address_dict):
        """ Tests that bag_validated is set to True when a valid location is provided and that
        the address is replaced with the suggested address. The original address should be saved
        in the extra_properties of the Location object """

        original_address = self.create_initial_data["location"]["address"]
        suggested_address = self.create_initial_data["location"]["address"]
        suggested_address["openbare_ruimte"] = "Amsteltje"
        validate_address_dict.return_value = suggested_address

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
        response_json = self.client.get(data['_links']['self']['href']).json()
        self.assertJsonSchema(self.retrieve_signal_schema, response_json)

    @patch("signals.apps.api.v1.validation.AddressValidation.validate_address_dict")
    def test_create_initial_valid_location_but_no_address(self, validate_address_dict):
        """Tests that a Signal can be created when loccation has no known address but
        coordinates are known."""
        del self.create_initial_data["location"]["address"]

        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')
        self.assertEqual(response.status_code, 201)
        validate_address_dict.assert_not_called()

        signal_id = response.data['id']
        signal = Signal.objects.get(id=signal_id)

        self.assertEqual(signal.location.bag_validated, False)

        # JSONSchema validation
        response_json = self.client.get(response.json()['_links']['self']['href']).json()
        self.assertJsonSchema(self.retrieve_signal_schema, response_json)

    @patch("signals.apps.api.v1.validation.AddressValidation.validate_address_dict",
           side_effect=AddressValidationUnavailableException)
    def test_create_initial_address_validation_unavailable(self, validate_address_dict):
        """ Tests that the signal is created even though the address validation service is
        unavailable. Should set bag_validated to False """
        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')
        self.assertEqual(response.status_code, 201)

        signal_id = response.data['id']
        signal = Signal.objects.get(id=signal_id)

        # Signal should be added, but bag_validated should be False
        self.assertFalse(signal.location.bag_validated)

        # JSONSchema validation
        response_json = self.client.get(response.json()['_links']['self']['href']).json()
        self.assertJsonSchema(self.retrieve_signal_schema, response_json)

    @patch("signals.apps.api.v1.validation.AddressValidation.validate_address_dict",
           side_effect=AddressValidationUnavailableException)
    def test_create_initial_try_update_bag_validated(self, validate_address_dict):
        """ Tests that the bag_validated field cannot be set manually, and that the address
        validation is called """
        data = self.create_initial_data
        data['location']['bag_validated'] = True
        response = self.client.post(self.list_endpoint, data, format='json')

        validate_address_dict.assert_called_once()

        self.assertEqual(response.status_code, 201)

        signal_id = response.data['id']
        signal = Signal.objects.get(id=signal_id)

        self.assertFalse(signal.location.bag_validated)

        # JSONSchema validation
        response_json = self.client.get(response.json()['_links']['self']['href']).json()
        self.assertJsonSchema(self.retrieve_signal_schema, response_json)

    @patch("signals.apps.api.v1.validation.AddressValidation.validate_address_dict",
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_initial_and_upload_image(self, validate_address_dict):
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

    @patch("signals.apps.api.v1.validation.AddressValidation.validate_address_dict")
    def test_update_location(self, validate_address_dict):
        # Partial update to update the location, all interaction via API.
        detail_endpoint = self.detail_endpoint.format(pk=self.signal_no_image.id)
        history_endpoint = self.history_endpoint.format(pk=self.signal_no_image.id)

        # check that only one Location is in the history
        querystring = urlencode({'what': 'UPDATE_LOCATION'})
        response = self.client.get(history_endpoint + '?' + querystring)
        self.assertEqual(len(response.json()), 1)

        # retrieve relevant fixture
        fixture_file = os.path.join(THIS_DIR, 'request_data', 'update_location.json')
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

    @patch("signals.apps.api.v1.validation.AddressValidation.validate_address_dict")
    def test_update_location_no_address(self, validate_address_dict):
        # Partial update to update the location, all interaction via API.
        # SIA must also allow location updates without known address but with
        # known coordinates.
        detail_endpoint = self.detail_endpoint.format(pk=self.signal_no_image.id)
        history_endpoint = self.history_endpoint.format(pk=self.signal_no_image.id)

        # check that only one Location is in the history
        querystring = urlencode({'what': 'UPDATE_LOCATION'})
        response = self.client.get(history_endpoint + '?' + querystring)
        self.assertEqual(len(response.json()), 1)

        # retrieve relevant fixture
        fixture_file = os.path.join(THIS_DIR, 'request_data', 'update_location.json')
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

    @patch("signals.apps.api.v1.validation.AddressValidation.validate_address_dict")
    def test_update_location_no_coordinates(self, validate_address_dict):
        # Partial update to update the location, all interaction via API.
        # SIA must also allow location updates without known address but with
        # known coordinates.
        detail_endpoint = self.detail_endpoint.format(pk=self.signal_no_image.id)
        history_endpoint = self.history_endpoint.format(pk=self.signal_no_image.id)

        # check that only one Location is in the history
        querystring = urlencode({'what': 'UPDATE_LOCATION'})
        response = self.client.get(history_endpoint + '?' + querystring)
        self.assertEqual(len(response.json()), 1)

        # retrieve relevant fixture
        fixture_file = os.path.join(THIS_DIR, 'request_data', 'update_location.json')
        with open(fixture_file, 'r') as f:
            data = json.load(f)
        del data['location']['geometrie']

        # update location
        response = self.client.patch(detail_endpoint, data, format='json')
        self.assertEqual(response.status_code, 400)
        validate_address_dict.assert_not_called()

    def test_update_status(self):
        # Partial update to update the status, all interaction via API.
        detail_endpoint = self.detail_endpoint.format(pk=self.signal_no_image.id)
        history_endpoint = self.history_endpoint.format(pk=self.signal_no_image.id)

        # check that only one Status is in the history
        querystring = urlencode({'what': 'UPDATE_STATUS'})
        response = self.client.get(history_endpoint + '?' + querystring)
        self.assertEqual(len(response.json()), 1)

        # retrieve relevant fixture
        fixture_file = os.path.join(THIS_DIR, 'request_data', 'update_status.json')
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
        response = self.client.patch(detail_endpoint, data, format='json')
        self.assertEqual(400, response.status_code)

        # check that the Status is there
        response = self.client.get(history_endpoint)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

        # JSONSchema validation
        response_json = response.json()
        self.assertJsonSchema(self.list_history_schema, response_json)

    def test_update_status_target_api_SIG1140(self):
        self.client.force_authenticate(user=self.superuser)
        detail_endpoint = self.detail_endpoint.format(pk=self.signal_no_image.id)

        data = {
            'status': {
                'state': 'ready to send',
                'text': 'Te verzenden naar THOR',
                'target_api': 'sigmax',
            }
        }
        response = self.client.patch(detail_endpoint, data, format='json')

        self.assertEqual(200, response.status_code)

        self.client.force_authenticate(user=self.sia_read_write_user)

    def test_send_to_sigmax_no_permission(self):
        detail_endpoint = self.detail_endpoint.format(pk=self.signal_no_image.id)

        data = {
            'status': {
                'state': 'ready to send',
                'text': 'Te verzenden naar THOR',
                'target_api': 'sigmax',
            }
        }
        response = self.client.patch(detail_endpoint, data, format='json')

        self.assertEqual(403, response.status_code)

    def test_update_status_with_required_text(self):
        """ Status change to 'afgehandeld' (o) requires text. When no text is supplied, a 400 should
        be returned """
        fixture_file = os.path.join(THIS_DIR, 'request_data', 'update_status.json')

        with open(fixture_file, 'r') as f:
            data = json.load(f)

        data["status"]["state"] = "o"
        del data["status"]["text"]

        response = self.client.patch(self.detail_endpoint.format(pk=self.signal_no_image.id), data,
                                     format='json')
        self.assertEqual(400, response.status_code)

    def test_update_category_assignment(self):
        # Partial update to update the location, all interaction via API.
        detail_endpoint = self.detail_endpoint.format(pk=self.signal_no_image.id)
        history_endpoint = self.history_endpoint.format(pk=self.signal_no_image.id)

        # check that only one category assignment is in the history
        querystring = urlencode({'what': 'UPDATE_CATEGORY_ASSIGNMENT'})
        response = self.client.get(history_endpoint + '?' + querystring)
        self.assertEqual(len(response.json()), 1)

        # retrieve relevant fixture
        fixture_file = os.path.join(THIS_DIR, 'request_data', 'update_category_assignment.json')
        with open(fixture_file, 'r') as f:
            data = json.load(f)

        del(data['category']['sub_category'])
        data['category']['category_url'] = self.link_subcategory

        response = self.client.patch(detail_endpoint, data, format='json')
        self.assertEqual(response.status_code, 200)

        # check that there are two category assignments in the history
        self.signal_no_image.refresh_from_db()

        response = self.client.get(history_endpoint + '?' + querystring)
        response_json = response.json()

        self.assertEqual(len(response_json), 2)
        self.assertEqual(response_json[0]['description'], data['category']['text'])

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
        detail_endpoint = self.detail_endpoint.format(pk=self.signal_no_image.id)

        # retrieve relevant fixture
        fixture_file = os.path.join(THIS_DIR, 'request_data', 'update_category_assignment.json')
        with open(fixture_file, 'r') as f:
            data = json.load(f)
        del(data['category']['sub_category'])
        data['category']['category_url'] = self.link_subcategory

        Signal.actions.update_category_assignment({'category': self.subcategory},
                                                  self.signal_no_image)
        self.signal_no_image.refresh_from_db()

        # Signal is initialised with a known category.
        cat_assignments_cnt = self.signal_no_image.category_assignments.count()

        # Update signal with same category
        response = self.client.patch(detail_endpoint, data, format='json')
        self.assertEqual(response.status_code, 200)

        # No category assignment should be added
        self.assertEqual(cat_assignments_cnt, self.signal_no_image.category_assignments.count())

    def test_update_priority(self):
        # Partial update to update the priority, all interaction via API.
        detail_endpoint = self.detail_endpoint.format(pk=self.signal_no_image.id)
        history_endpoint = self.history_endpoint.format(pk=self.signal_no_image.id)

        # check that only one Priority is in the history
        querystring = urlencode({'what': 'UPDATE_PRIORITY'})
        response = self.client.get(history_endpoint + '?' + querystring)
        self.assertEqual(len(response.json()), 1)

        # retrieve relevant fixture
        fixture_file = os.path.join(THIS_DIR, 'request_data', 'update_priority.json')
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
        detail_endpoint = self.detail_endpoint.format(pk=self.signal_no_image.id)
        history_endpoint = self.history_endpoint.format(pk=self.signal_no_image.id)

        # check that there is no Note the history
        querystring = urlencode({'what': 'CREATE_NOTE'})
        response = self.client.get(history_endpoint + '?' + querystring)
        self.assertEqual(len(response.json()), 0)

        # retrieve relevant fixture
        fixture_file = os.path.join(THIS_DIR, 'request_data', 'create_note.json')
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
        detail_endpoint = self.detail_endpoint.format(pk=self.signal_no_image.id)
        response = self.client.put(detail_endpoint, {}, format='json')
        self.assertEqual(response.status_code, 405)

    def test_split(self):
        self.assertEqual(Signal.objects.count(), 2)
        response = self.client.post(
            self.split_endpoint.format(pk=self.signal_no_image.id),
            [
                {
                    'text': 'Child #1',
                    'category': {'category_url': self.link_subcategory}
                },
                {
                    'text': 'Child #2',
                    'category': {'sub_category': self.link_subcategory}
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

            response_json = response.json()
            for key in [
                'status', 'category', 'priority', 'location', 'reporter', 'notes', 'has_attachments'
            ]:
                self.assertIn(key, response_json)

        self.assertEqual(4, Signal.objects.count())

        self.signal_no_image.refresh_from_db()
        self.assertEqual(2, len(self.signal_no_image.children.all()))
        self.assertEqual(self.sia_read_write_user.email, self.signal_no_image.status.created_by)

    def test_split_children_must_inherit_these_properties(self):
        """When a signal is split its children must inherit certain properties."""
        # Split the signal, take note of the returned children
        response = self.client.post(
            self.split_endpoint.format(pk=self.signal_no_image.id),
            [
                {
                    'text': 'Child #1',
                    'category': {'sub_category': self.link_subcategory}
                },
                {
                    'text': 'Child #2',
                    'category': {'sub_category': self.link_subcategory}
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
            self.assertEqual(parent_json['location']['address_text'],
                             child_json['location']['address_text'])
            self.assertEqual(parent_json['location']['address'],
                             child_json['location']['address'])
            self.assertEqual(parent_json['location']['geometrie'],
                             child_json['location']['geometrie'])

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
                self.subcategory.slug
            )
            self.assertEqual(
                child_json['category']['main_slug'],
                self.subcategory.parent.slug
            )

        self.signal_no_image.refresh_from_db()
        self.assertEqual(self.sia_read_write_user.email, self.signal_no_image.status.created_by)

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
                    'category': {'sub_category': self.link_subcategory}
                },
                {
                    'text': 'Child #2',
                    'reuse_parent_image': True,
                    'category': {'sub_category': self.link_subcategory}
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

        self.signal_with_image.refresh_from_db()
        self.assertEqual(self.sia_read_write_user.email, self.signal_with_image.status.created_by)

    def test_split_children_must_inherit_parent_images_for_1st_child(self):
        # Split the signal, take note of the returned children
        response = self.client.post(
            self.split_endpoint.format(pk=self.signal_with_image.id),
            [
                {
                    'text': 'Child #1',
                    'reuse_parent_image': True,
                    'category': {'sub_category': self.link_subcategory}
                },
                {
                    'text': 'Child #2',
                    'category': {'sub_category': self.link_subcategory}
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

        self.assertEqual(self.sia_read_write_user.email, self.signal_with_image.status.created_by)

    def _create_split_signal(self):
        parent_signal = SignalFactory.create()
        split_data = [
            {
                "text": "Child signal 1",
                'category': {'sub_category': self.subcategory}
            },
            {
                "text": "Child signal 2",
                'category': {'sub_category': self.subcategory}
            }
        ]
        Signal.actions.split(split_data, parent_signal)

        return parent_signal

    def test_split_get_split_signal(self):
        """ A GET /<signal_id>/split on a split signal should return a 200 with its
        children in the response body """
        signal = self._create_split_signal()
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
        response = self.client.get(self.split_endpoint.format(pk=signal.pk))
        self.assertEqual(404, response.status_code)

    def test_split_post_split_signal(self):
        """ A POST /<signal_id>/split on an already updated signal should return a 412 """
        signal = self._create_split_signal()
        data = [{"text": "Child 1"}, {"text": "Child 2"}]
        response = self.client.post(self.split_endpoint.format(pk=signal.pk), data, format='json')
        self.assertEqual(412, response.status_code)
        self.assertEqual("Signal has already been split", response.json()["detail"])

    def test_child_cannot_be_split(self):
        """Child signals cannot themselves have children (i.e. not be split)."""
        response = self.client.post(
            self.split_endpoint.format(pk=self.signal_no_image.id),
            [
                {
                    'text': 'Child #1',
                    'category': {'sub_category': self.link_subcategory}
                },
                {
                    'text': 'Child #2',
                    'category': {'sub_category': self.link_subcategory}
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
            response = self.client.post(
                self.split_endpoint.format(pk=item['id']),
                [
                    {
                        'text': 'Child #1',
                        'category': {'sub_category': self.link_subcategory}
                    },
                    {
                        'text': 'Child #2',
                        'category': {'category_url': self.link_subcategory}
                    }
                ],
                format='json',
            )
            self.assertEqual(response.status_code, 412)

    def test_split_empty_data(self):
        self.assertEqual(Signal.objects.count(), 2)

        response = self.client.post(
            self.split_endpoint.format(pk=self.signal_no_image.id),
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
        self.assertEqual(Signal.objects.count(), 2)

        response = self.client.post(
            self.split_endpoint.format(pk=self.signal_no_image.id),
            [
                {
                    'text': 'Child #1',
                    'category': {'sub_category': self.link_subcategory}
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
        self.assertEqual(Signal.objects.count(), 2)

        response = self.client.post(
            self.split_endpoint.format(pk=self.signal_no_image.id),
            [
                {
                    'text': 'Child #1',
                    'category': {'sub_category': self.link_subcategory}
                },
                {
                    'text': 'Child #2',
                    'category': {'category_url': self.link_subcategory}
                },
                {
                    'text': 'Child #3',
                    'category': {'sub_category': self.link_subcategory}
                },
                {
                    'text': 'Child #4',
                    'category': {'category_url': self.link_subcategory}
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

    def test_removed_from_category(self):
        after = timezone.now() - timedelta(minutes=10)
        querystring = urlencode({
            'category_slug': self.signal_no_image.category_assignment.category.slug,
            'after': after.isoformat()
        })
        endpoint = '{}?{}'.format(
            self.removed_from_category_endpoint,
            querystring
        )

        # The category has not been changed over the last 10 minutes
        response = self.client.get(endpoint, format='json')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['count'], 0)

        # Change the category
        new_category = CategoryFactory.create()
        Signal.actions.update_category_assignment({'category': new_category}, self.signal_no_image)

        # Now we should get the signal_no_image in the response because we changed the category
        response = self.client.get(endpoint, format='json')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['id'], self.signal_no_image.id)

    def test_removed_from_category_but_reassigned(self):
        after = timezone.now() - timedelta(minutes=10)
        querystring = urlencode({
            'category_slug': self.signal_no_image.category_assignment.category.slug,
            'after': after.isoformat()
        })
        endpoint = '{}?{}'.format(
            self.removed_from_category_endpoint,
            querystring
        )

        # The category has not been changed over the last 10 minutes
        response = self.client.get(endpoint, format='json')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['count'], 0)

        # Change the category
        prev_category = self.signal_no_image.category_assignment.category
        new_category = CategoryFactory.create()
        Signal.actions.update_category_assignment({'category': new_category},
                                                  self.signal_no_image)
        Signal.actions.update_category_assignment({'category': prev_category},
                                                  self.signal_no_image)

        # Still should not get the signal_no_image in the response because we changed the category
        # back to the original category
        response = self.client.get(endpoint, format='json')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['count'], 0)

    def test_removed_from_category_date_range(self):
        with freeze_time(timezone.now() - timedelta(minutes=5)):
            after = timezone.now() - timedelta(minutes=5)
            before = timezone.now() + timedelta(minutes=5)
            querystring = urlencode({
                'category_slug': self.signal_no_image.category_assignment.category.slug,
                'after': after.isoformat(),
                'before': before.isoformat()
            })
            endpoint = '{}?{}'.format(
                self.removed_from_category_endpoint,
                querystring
            )

            # Change the category
            new_category = CategoryFactory.create()
            Signal.actions.update_category_assignment({'category': new_category},
                                                      self.signal_no_image)

            # Now we should get the signal_no_image in the response because we changed the category
            response = self.client.get(endpoint, format='json')
            self.assertEqual(response.status_code, 200)

            data = response.json()
            self.assertEqual(data['count'], 1)
            self.assertEqual(data['results'][0]['id'], self.signal_no_image.id)

    def test_removed_from_category_out_of_date_range(self):
        after = timezone.now() - timedelta(minutes=5)
        before = timezone.now() + timedelta(minutes=5)
        querystring = urlencode({
            'category': self.signal_no_image.category_assignment.category.slug,
            'after': after.isoformat(),
            'before': before.isoformat()
        })
        endpoint = '{}?{}'.format(
            self.removed_from_category_endpoint,
            querystring
        )

        with freeze_time(timezone.now() - timedelta(minutes=10)):
            # Change the category
            new_category = CategoryFactory.create()
            Signal.actions.update_category_assignment({'category': new_category},
                                                      self.signal_no_image)

            # Now we should get the signal_no_image in the response because we changed the category
            response = self.client.get(endpoint, format='json')
            self.assertEqual(response.status_code, 200)

            data = response.json()
            self.assertEqual(data['count'], 0)

    def test_update_location_renders_correctly_in_history(self):
        """Test that location updates have correct description field in history.

        Valid addresses in SIA have:
        - coordinates and address
        - only cooordinates

        Furthermore locations without stadsdeel property should render as well.
        """
        detail_endpoint = self.detail_endpoint.format(pk=self.signal_no_image.id)

        # Prepare the data for the 3 types of Location updates
        update_location_json = os.path.join(THIS_DIR, 'request_data', 'update_location.json')
        with open(update_location_json, 'r') as f:
            data_with_address = json.load(f)
        data_no_address = copy.deepcopy(data_with_address)
        data_no_address['location']['address'] = {}
        data_no_address_no_stadsdeel = copy.deepcopy(data_no_address)
        data_no_address_no_stadsdeel['location']['stadsdeel'] = None

        history_endpoint = self.history_endpoint.format(pk=self.signal_no_image.id)
        # Test full location (address and coordinates) case:
        response = self.client.patch(detail_endpoint, data=data_with_address, format='json')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(history_endpoint + '?what=UPDATE_LOCATION')
        response_data = response.json()
        self.assertEqual(len(response_data), 2)
        self.assertEqual(
            'Stadsdeel: Centrum\nDe Ruijterkade 36A\nAmsterdam',
            response_data[0]['description']
        )

        # Test no address case:
        response = self.client.patch(detail_endpoint, data=data_no_address, format='json')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(history_endpoint + '?what=UPDATE_LOCATION')
        response_data = response.json()
        self.assertEqual(len(response_data), 3)
        self.assertIn(
            'Stadsdeel: Centrum',
            response_data[0]['description']
        )
        self.assertIn('52', response_data[0]['description'])  # no string compares on floats

        # Test no address and no address
        response = self.client.patch(
            detail_endpoint, data=data_no_address_no_stadsdeel, format='json')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(history_endpoint + '?what=UPDATE_LOCATION')
        response_data = response.json()
        self.assertEqual(len(response_data), 4)
        self.assertNotIn(
            'Stadsdeel:',
            response_data[0]['description']
        )
        self.assertIn('52', response_data[0]['description'])  # no string compares on floats
        self.assertIn('Locatie is gepind op de kaart', response_data[0]['description'])

    @patch("signals.apps.api.v1.serializers.PrivateSignalSerializerList.create")
    def test_post_django_validation_error_to_drf_validation_error(self, mock):
        mock.side_effect = ValidationError('this is a test')

        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(1, len(response.json()))
        self.assertEqual('this is a test', response.json()[0])

    @patch("signals.apps.api.v1.serializers.PrivateSignalSerializerDetail.update")
    def test_patch_django_validation_error_to_drf_validation_error(self, mock):
        detail_endpoint = self.detail_endpoint.format(pk=self.signal_no_image.id)

        # retrieve relevant fixture
        fixture_file = os.path.join(THIS_DIR, 'request_data', 'update_status.json')
        with open(fixture_file, 'r') as f:
            data = json.load(f)

        mock.side_effect = ValidationError('this is a test')

        response = self.client.patch(detail_endpoint, data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(1, len(response.json()))
        self.assertEqual('this is a test', response.json()[0])

    def test_patch_multiple_response_most_recent(self):
        """
        Signal returned from detail endpoint after PATCH must be up to date.
        """
        detail_endpoint = self.detail_endpoint.format(pk=self.signal_no_image.id)
        response = self.client.get(detail_endpoint)
        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        cat_url_before = response_data['category']['category_url']
        state_before = response_data['status']['state']

        SOME_MESSAGE_A = 'SOME MESSAGE A'
        SOME_MESSAGE_B = 'SOME MESSAGE B'
        payload = {
            'status': {
                'state': workflow.BEHANDELING,  # StatusFactory always uses workflow.GEMELD
                'text': SOME_MESSAGE_A,
            },
            'category': {
                'sub_category': self.link_subcategory,
                'text': SOME_MESSAGE_B,
            }
        }

        response = self.client.patch(detail_endpoint, data=payload, format='json')
        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        self.assertNotEqual(cat_url_before, response_data['category']['category_url'])
        self.assertEqual(SOME_MESSAGE_B, response.data['category']['text'])
        self.assertNotEqual(state_before, response_data['status']['state'])
        self.assertEqual(SOME_MESSAGE_A, response.data['status']['text'])

    def test_create_with_invalid_source_user(self):
        data = self.create_initial_data
        data['source'] = 'online'
        response = self.client.post(self.list_endpoint, data, format='json')

        self.assertEqual(400, response.status_code)
        self.assertEqual(response.json()['source'][0],
                         'Invalid source given for authenticated user')

    def test_validate_extra_properties_enabled(self):
        initial_data = self.create_initial_data
        initial_data['extra_properties'] = [{
            'id': 'test_id',
            'label': 'test_label',
            'answer': {
                'id': 'test_answer',
                'value': 'test_value'
            },
            'category_url': self.link_subcategory
        }, {
            'id': 'test_id',
            'label': 'test_label',
            'answer': 'test_answer',
            'category_url': self.link_subcategory
        }, {
            'id': 'test_id',
            'label': 'test_label',
            'answer': ['a', 'b', 'c'],
            'category_url': self.link_subcategory
        }]

        response = self.client.post(self.list_endpoint, initial_data, format='json')

        self.assertEqual(201, response.status_code)
        self.assertEqual(3, Signal.objects.count())

    def test_validate_extra_properties_enabled_invalid_data(self):
        initial_data = self.create_initial_data
        initial_data['extra_properties'] = {'old_style': 'extra_properties'}

        response = self.client.post(self.list_endpoint, initial_data, format='json')
        data = response.json()

        self.assertEqual(400, response.status_code)
        self.assertIn('extra_properties', data)
        self.assertEqual(data['extra_properties'][0], 'Invalid input.')
        self.assertEqual(2, Signal.objects.count())


class TestPrivateSignalAttachments(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    list_endpoint = '/signals/v1/private/signals/'
    detail_endpoint = list_endpoint + '{}'
    attachment_endpoint = detail_endpoint + '/attachments'
    test_host = 'http://testserver'

    def setUp(self):
        self.signal = SignalFactory.create()

        fixture_file = os.path.join(THIS_DIR, 'request_data', 'create_initial.json')
        with open(fixture_file, 'r') as f:
            self.create_initial_data = json.load(f)
        self.create_initial_data['source'] = 'valid-source'

        self.client.force_authenticate(user=self.sia_read_write_user)

    def test_image_upload(self):
        endpoint = self.attachment_endpoint.format(self.signal.id)
        image = SimpleUploadedFile('image.gif', small_gif, content_type='image/gif')

        response = self.client.post(endpoint, data={'file': image})

        self.assertEqual(response.status_code, 201)
        self.assertIsInstance(self.signal.attachments.first(), Attachment)
        self.assertIsInstance(self.signal.attachments.filter(is_image=True).first(), Attachment)

    def test_attachment_upload(self):
        endpoint = self.attachment_endpoint.format(self.signal.id)
        doc_upload = os.path.join(SIGNALS_TEST_DIR, 'sia-ontwerp-testfile.doc')

        with open(doc_upload, encoding='latin-1') as f:
            data = {"file": f}

            response = self.client.post(endpoint, data)

        self.assertEqual(response.status_code, 201)
        self.assertIsInstance(self.signal.attachments.first(), Attachment)
        self.assertIsNone(self.signal.attachments.filter(is_image=True).first())
        self.assertEqual(self.sia_read_write_user.email, self.signal.attachments.first().created_by)

    def test_create_has_attachments_false(self):
        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')
        self.assertEqual(response.status_code, 201)

        data = response.json()
        self.assertFalse(data['has_attachments'])

    def test_has_attachments_true(self):
        non_image_attachments = add_non_image_attachments(self.signal, 1)
        image_attachments = add_image_attachments(self.signal, 2)
        non_image_attachments += add_non_image_attachments(self.signal, 1)

        total_attachments = len(non_image_attachments) + len(image_attachments)

        endpoint = self.detail_endpoint.format(self.signal.pk)
        response = self.client.get(endpoint, format='json')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data['has_attachments'])

        attachment_endpoint = data['_links']['sia:attachments']['href']

        response = self.client.get(attachment_endpoint, format='json')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['count'], total_attachments)
        self.assertEqual(len(data['results']), total_attachments)

        self.assertFalse(data['results'][0]['is_image'])
        self.assertEqual(self.test_host + non_image_attachments[0].file.url,
                         data['results'][0]['location'])

        self.assertTrue(data['results'][1]['is_image'])
        self.assertEqual(self.test_host + image_attachments[0].file.url,
                         data['results'][1]['location'])

        self.assertTrue(data['results'][2]['is_image'])
        self.assertEqual(self.test_host + image_attachments[1].file.url,
                         data['results'][2]['location'])

        self.assertFalse(data['results'][3]['is_image'])
        self.assertEqual(self.test_host + non_image_attachments[1].file.url,
                         data['results'][3]['location'])


@freeze_time('2019-11-01 12:00:00', tz_offset=1)
@override_settings(FEATURE_FLAGS=dict(
    PERMISSION_SIAPERMISSIONS=True,
    PERMISSION_SPLITPERMISSION=True,
    PERMISSION_SIGNALCREATEINITIALPERMISSION=True,
    PERMISSION_SIGNALCREATENOTEPERMISSION=True,
    PERMISSION_SIGNALCHANGESTATUSPERMISSION=True,
    PERMISSION_SIGNALCHANGECATEGORYPERMISSION=True,
    PERMISSION_DEPARTMENTS=True,
))  # Enable all permission feature flags
class TestPrivateSignalViewSetPermissions(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    list_endpoint = '/signals/v1/private/signals/'
    detail_endpoint = '/signals/v1/private/signals/{pk}'
    history_endpoint = '/signals/v1/private/signals/{pk}/history'
    split_endpoint = '/signals/v1/private/signals/{pk}/split'

    category_url_pattern = '/signals/v1/public/terms/categories/{}'
    subcategory_url_pattern = '/signals/v1/public/terms/categories/{}/sub_categories/{}'

    def setUp(self):
        self.department = DepartmentFactory.create(
            code='TST',
            name='Department for testing #1',
            is_intern=False,
        )

        self.category = ParentCategoryFactory.create()
        self.subcategory = CategoryFactory.create(
            parent=self.category,
            departments=[self.department],
        )
        self.subcategory_2 = CategoryFactory.create(
            parent=self.category,
        )

        self.signal = SignalFactoryValidLocation.create(
            category_assignment__category=self.subcategory,
            reporter=None,
            incident_date_start=timezone.now(),
            incident_date_end=timezone.now() + timedelta(hours=1),
            source='test-api',
        )

        self.signal_2 = SignalFactoryValidLocation.create(
            category_assignment__category=self.subcategory_2,
            reporter=None,
            incident_date_start=timezone.now(),
            incident_date_end=timezone.now() + timedelta(hours=1),
            source='test-api',
        )

        self.link_category = self.category_url_pattern.format(
            self.category.slug
        )
        self.link_subcategory = self.subcategory_url_pattern.format(
            self.category.slug, self.subcategory.slug
        )
        self.link_subcategory_2 = self.subcategory_url_pattern.format(
            self.category.slug, self.subcategory_2.slug
        )

        self.sia_user = self.sia_read_write_user
        self.sia_user.profile.departments.add(self.department)
        self.sia_user.save()

        self.create_initial_permission = Permission.objects.get(
            codename='sia_signal_create_initial'
        )
        self.create_note_permission = Permission.objects.get(
            codename='sia_signal_create_note'
        )
        self.change_status_permission = Permission.objects.get(
            codename='sia_signal_change_status'
        )
        self.change_category_permission = Permission.objects.get(
            codename='sia_signal_change_category'
        )

        self.test_group = GroupFactory.create(name='Test Group')

        self.test_group.permissions.add(self.create_initial_permission)
        self.test_group.permissions.add(self.create_note_permission)
        self.test_group.permissions.add(self.change_category_permission)
        self.test_group.permissions.add(self.change_status_permission)

    def test_get_endpoints(self):
        self.client.force_authenticate(user=self.sia_user)

        endpoints = (
            self.list_endpoint,
            self.detail_endpoint.format(pk=self.signal.pk),
            self.history_endpoint.format(pk=self.signal.pk),
        )

        for endpoint in endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 200, msg='{}'.format(endpoint))

    def test_create_initial_forbidden(self):
        self.client.force_authenticate(user=self.sia_user)

        data = {
            'text': 'Er liggen losse stoeptegels op het trottoir',
            'category': {
                'sub_category': self.link_subcategory,
            },
            'location': {},
            'reporter': {},
            'incident_date_start': timezone.now(),
            'source': 'test-api',
        }
        response = self.client.post(self.list_endpoint, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_initial(self):
        self.sia_user.user_permissions.add(self.create_initial_permission)
        self.client.force_authenticate(user=self.sia_user)

        data = {
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
        response = self.client.post(self.list_endpoint, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_note_forbidden(self):
        self.client.force_authenticate(user=self.sia_user)

        detail_endpoint = self.detail_endpoint.format(pk=self.signal.id)
        data = {'notes': [{'text': 'This is a text for a note.'}]}
        response = self.client.patch(detail_endpoint, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_note(self):
        self.assertEqual(self.signal.notes.count(), 0)

        self.sia_user.user_permissions.add(self.create_note_permission)
        self.client.force_authenticate(user=self.sia_user)

        detail_endpoint = self.detail_endpoint.format(pk=self.signal.id)
        data = {'notes': [{'text': 'This is a text for a note.'}]}
        response = self.client.patch(detail_endpoint, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.signal.refresh_from_db()

        self.assertEqual(self.signal.notes.count(), 1)
        self.assertEqual(self.signal.notes.first().created_by, self.sia_user.email)

    def test_change_status_forbidden(self):
        self.client.force_authenticate(user=self.sia_user)

        detail_endpoint = self.detail_endpoint.format(pk=self.signal.id)
        data = {
            'status': {
                'text': 'Test status update',
                'state': 'b'
            }
        }
        response = self.client.patch(detail_endpoint, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_change_status(self):
        self.sia_user.user_permissions.add(self.change_status_permission)
        self.client.force_authenticate(user=self.sia_user)

        detail_endpoint = self.detail_endpoint.format(pk=self.signal.id)
        data = {
            'status': {
                'text': 'Test status update',
                'state': 'b'
            }
        }
        response = self.client.patch(detail_endpoint, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.signal.refresh_from_db()

        self.assertEqual(self.signal.status.state, 'b')
        self.assertEqual(self.signal.status.user, self.sia_user.email)

    def test_change_category_forbidden(self):
        self.client.force_authenticate(user=self.sia_user)

        detail_endpoint = self.detail_endpoint.format(pk=self.signal.id)
        data = {
            'category': {
                'text': 'Update category test',
                'sub_category': self.link_subcategory_2
            }
        }
        response = self.client.patch(detail_endpoint, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_change_category(self):
        self.assertEqual(self.signal.category_assignment.category.pk, self.subcategory.pk)

        self.sia_user.user_permissions.add(self.change_category_permission)
        self.client.force_authenticate(user=self.sia_user)

        detail_endpoint = self.detail_endpoint.format(pk=self.signal.id)
        data = {
            'category': {
                'text': 'Update category test',
                'sub_category': self.link_subcategory_2
            }
        }
        response = self.client.patch(detail_endpoint, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.signal.refresh_from_db()

        self.assertEqual(self.signal.category_assignment.category.pk, self.subcategory_2.pk)
        self.assertEqual(self.signal.category_assignment.created_by, self.sia_user.email)

    @patch('signals.apps.api.v1.validation.AddressValidation.validate_address_dict')
    def test_update_location(self, validate_address_dict):
        self.client.force_authenticate(user=self.sia_user)

        detail_endpoint = self.detail_endpoint.format(pk=self.signal.id)
        data = {
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

        validated_address = copy.deepcopy(data['location']['address'])
        validate_address_dict.return_value = validated_address

        response = self.client.patch(detail_endpoint, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.signal.refresh_from_db()

        self.assertEqual(self.signal.location.created_by, self.sia_user.email)

    def test_create_initial_role_based_permission(self):
        self.sia_user.groups.add(self.test_group)
        self.client.force_authenticate(user=self.sia_user)

        data = {
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
        response = self.client.post(self.list_endpoint, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_multiple_actions_role_based_permission(self):
        self.sia_user.groups.add(self.test_group)
        self.client.force_authenticate(user=self.sia_user)

        detail_endpoint = self.detail_endpoint.format(pk=self.signal.id)
        data = {
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
        response = self.client.patch(detail_endpoint, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_category_method_not_allowed(self):
        self.assertEqual(self.signal.category_assignment.category.pk, self.subcategory.pk)

        self.sia_user.user_permissions.add(self.change_category_permission)
        self.client.force_authenticate(user=self.sia_user)

        detail_endpoint = self.detail_endpoint.format(pk=self.signal.id)
        data = {
            'category': {
                'text': 'Update category test',
                'sub_category': self.link_subcategory_2
            }
        }
        response = self.client.delete(detail_endpoint, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        self.signal.refresh_from_db()

        self.assertEqual(self.signal.category_assignment.category.pk, self.subcategory.pk)

    def test_get_signals(self):
        self.client.force_authenticate(user=self.sia_user)

        response = self.client.get(self.list_endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['count'], Signal.objects.filter_for_user(user=self.sia_user).count())
        self.assertNotEqual(data['count'], Signal.objects.count())
        self.assertEqual(2, Signal.objects.count())

    def test_change_category_to_other_category_in_other_department(self):
        self.sia_user.user_permissions.add(self.change_category_permission)
        self.client.force_authenticate(user=self.sia_user)

        response = self.client.get(self.list_endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['count'], Signal.objects.filter_for_user(user=self.sia_user).count())
        self.assertNotEqual(data['count'], Signal.objects.count())
        self.assertEqual(2, Signal.objects.count())

        detail_endpoint = self.detail_endpoint.format(pk=self.signal.id)
        data = {
            'category': {
                'text': 'Update category test',
                'sub_category': self.link_subcategory_2
            }
        }
        response = self.client.patch(detail_endpoint, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(self.list_endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data['count'], 0)
        self.assertEqual(data['count'], Signal.objects.filter_for_user(user=self.sia_user).count())
        self.assertNotEqual(data['count'], Signal.objects.count())
        self.assertEqual(2, Signal.objects.count())

    def test_get_signal_not_my_department(self):
        self.client.force_authenticate(user=self.sia_user)
        detail_endpoint = self.detail_endpoint.format(pk=self.signal_2.id)
        response = self.client.get(detail_endpoint)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_change_signal_not_my_department(self):
        self.sia_user.user_permissions.add(self.change_category_permission)
        self.client.force_authenticate(user=self.sia_user)

        data = {
            'category': {
                'text': 'Update category test',
                'sub_category': self.link_subcategory_2
            }
        }

        detail_endpoint = self.detail_endpoint.format(pk=self.signal_2.id)
        response = self.client.patch(detail_endpoint, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
