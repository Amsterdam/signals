import copy
import json
import os
from datetime import timedelta
from unittest import skip
from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.contrib.gis.geos import MultiPolygon, Polygon
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone
from django.utils.http import urlencode
from freezegun import freeze_time

from signals.apps.api.v1.validation.address.base import (
    AddressValidationUnavailableException,
    NoResultsException
)
from signals.apps.signals import workflow
from signals.apps.signals.factories import (
    AreaFactory,
    CategoryFactory,
    SignalFactory,
    SignalFactoryValidLocation,
    SignalFactoryWithImage
)
from signals.apps.signals.models import STADSDEEL_CENTRUM, Signal
from tests.apps.signals.attachment_helpers import small_gif
from tests.test import SIAReadWriteUserMixin, SignalsBaseApiTestCase

THIS_DIR = os.path.dirname(__file__)
SIGNALS_TEST_DIR = os.path.join(os.path.split(THIS_DIR)[0], '..', 'signals')


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

        self.sia_read_write_user.user_permissions.add(Permission.objects.get(codename='sia_can_view_all_categories'))
        self.client.force_authenticate(user=self.sia_read_write_user)

    def test_history_deelmeldingen(self):
        parent = SignalFactory.create()
        child_1 = SignalFactory.create(parent=parent)
        child_2 = SignalFactory.create(parent=parent)

        base_url = self.history_endpoint.format(pk=parent.id)
        querystring = urlencode({'what': 'CHILD_SIGNAL_CREATED'})
        response = self.client.get(base_url + '?' + querystring)

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # SIA should show 2 entries for child signals created
        self.assertEqual(len(data), 2)

        self.assertEqual(data[0]['identifier'], f'CHILD_SIGNAL_CREATED_{child_2.id}')
        self.assertEqual(data[0]['what'], 'CHILD_SIGNAL_CREATED')
        self.assertEqual(data[0]['action'], 'Deelmelding toegevoegd')
        self.assertEqual(data[0]['description'], f'Melding {child_2.id}')

        self.assertEqual(data[1]['identifier'], f'CHILD_SIGNAL_CREATED_{child_1.id}')
        self.assertEqual(data[1]['what'], 'CHILD_SIGNAL_CREATED')
        self.assertEqual(data[1]['action'], 'Deelmelding toegevoegd')
        self.assertEqual(data[1]['description'], f'Melding {child_1.id}')

        # JSONSchema validation
        self.assertJsonSchema(self.list_history_schema, data)

    def test_history_splitmeldingen(self):
        # While the split functionality is removed from SIA/Signalen there can
        # stil be `signal.Signal` instances that were split, and still have to
        # be handled or be shown in historical data.

        parent = SignalFactory.create(status__state='s')
        SignalFactory.create_batch(2, parent=parent)

        base_url = self.history_endpoint.format(pk=parent.id)
        querystring = urlencode({'what': 'CHILD_SIGNAL_CREATED'})
        response = self.client.get(base_url + '?' + querystring)

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # SIA should not show 2 entries because the Signal was split instead of "opgedeeld"
        self.assertEqual(len(data), 0)

    # -- write tests --
    def test_create_with_status(self):
        """ Tests that an error is returned when we try to set the status """
        self.create_initial_data["status"] = {
            "state": workflow.BEHANDELING,
            "text": "Invalid stuff happening here"
        }

        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')

        self.assertEqual(400, response.status_code)

    @patch("signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address",
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_initial_without_stadsdeel(self, validate_address):
        # Create initial Signal, check that it reached the database.
        signal_count = Signal.objects.count()

        create_initial_data = self.create_initial_data
        del(create_initial_data['location']['stadsdeel'])
        del(create_initial_data['location']['address'])
        del(create_initial_data['location']['buurt_code'])

        geometry = MultiPolygon([Polygon.from_bbox([4.877157, 52.357204, 4.929686, 52.385239])], srid=4326)
        AreaFactory.create(geometry=geometry, name='Centrum', code='centrum', _type__code='sia-stadsdeel')

        response = self.client.post(self.list_endpoint, create_initial_data, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Signal.objects.count(), signal_count + 1)

        # Check that the actions are logged with the correct user email
        new_url = response.json()['_links']['self']['href']
        response = self.client.get(new_url)
        response_json = response.json()

        # JSONSchema validation
        self.assertJsonSchema(self.retrieve_signal_schema, response_json)

        self.assertIsNotNone(response_json['location']['stadsdeel'])
        self.assertEqual(response_json['location']['stadsdeel'], STADSDEEL_CENTRUM)
        self.assertEqual(response_json['location']['created_by'], self.sia_read_write_user.email)

    @skip('Disabled for now, it no longer throws an error but logs a warning and stores the unvalidated address')
    @patch("signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address",
           side_effect=NoResultsException)
    def test_create_initial_invalid_location(self, validate_address):
        """ Tests that a 400 is returned when an invalid location is provided """
        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')

        self.assertEqual(response.status_code, 400)

    @patch("signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address")
    def test_create_initial_valid_location(self, validate_address):
        """ Tests that bag_validated is set to True when a valid location is provided and that
        the address is replaced with the suggested address. The original address should be saved
        in the extra_properties of the Location object """

        original_address = self.create_initial_data["location"]["address"]
        suggested_address = self.create_initial_data["location"]["address"]
        suggested_address["openbare_ruimte"] = "Amsteltje"
        validate_address.return_value = suggested_address

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

    @patch("signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address")
    def test_create_initial_valid_location_but_no_address(self, validate_address):
        """Tests that a Signal can be created when loccation has no known address but
        coordinates are known."""
        del self.create_initial_data["location"]["address"]

        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')
        self.assertEqual(response.status_code, 201)
        validate_address.assert_not_called()

        signal_id = response.data['id']
        signal = Signal.objects.get(id=signal_id)

        self.assertEqual(signal.location.bag_validated, False)

        # JSONSchema validation
        response_json = self.client.get(response.json()['_links']['self']['href']).json()
        self.assertJsonSchema(self.retrieve_signal_schema, response_json)

    @patch("signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address",
           side_effect=AddressValidationUnavailableException)
    def test_create_initial_address_validation_unavailable(self, validate_address):
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

    @patch("signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address",
           side_effect=AddressValidationUnavailableException)
    def test_create_initial_try_update_bag_validated(self, validate_address):
        """ Tests that the bag_validated field cannot be set manually, and that the address
        validation is called """
        self.create_initial_data['location']['bag_validated'] = True
        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')

        validate_address.assert_called_once()

        self.assertEqual(response.status_code, 201)

        signal_id = response.data['id']
        signal = Signal.objects.get(id=signal_id)

        self.assertFalse(signal.location.bag_validated)

        # JSONSchema validation
        response_json = self.client.get(response.json()['_links']['self']['href']).json()
        self.assertJsonSchema(self.retrieve_signal_schema, response_json)

    @patch("signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address",
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_initial_and_upload_image(self, validate_address):
        attachments_url = self.detail_endpoint.format(pk=self.signal_no_image.pk) + '/attachments/'

        image = SimpleUploadedFile('image.gif', small_gif, content_type='image/gif')
        response = self.client.post(attachments_url, data={'file': image})
        self.assertEqual(response.status_code, 201)

        # Check that a second upload is NOT rejected
        image2 = SimpleUploadedFile('image.gif', small_gif, content_type='image/gif')
        response = self.client.post(attachments_url, data={'file': image2})
        self.assertEqual(response.status_code, 201)

    @patch("signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address",
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_initial_with_type(self, validate_address):
        # Type should be present in serialization of created Signal if it is
        # provided on creation.
        # Create initial Signal.
        self.create_initial_data['type'] = {'code': 'REQ'}

        signal_count = Signal.objects.count()
        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Signal.objects.count(), signal_count + 1)

        # check that our new signal has a type
        response_json = response.json()
        pk = response_json['id']
        signal = Signal.objects.get(id=pk)
        self.assertEqual(signal.type_assignment.name, 'REQ')
        self.assertEqual(response_json['type']['code'], 'REQ')
        self.assertIn('created_at', response_json['type'])
        self.assertIn('created_by', response_json['type'])

        # JSONSchema validation
        new_url = response.json()['_links']['self']['href']
        response_json = self.client.get(new_url).json()
        self.assertJsonSchema(self.retrieve_signal_schema, response_json)

    @patch("signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address",
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_initial_without_type(self, validate_address):
        # Type should be present in serialization of created Signal, even if it
        # was not initially provided.
        # Create initial Signal.
        signal_count = Signal.objects.count()
        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Signal.objects.count(), signal_count + 1)

        # check that our new signal has a type
        response_json = response.json()
        pk = response_json['id']
        signal = Signal.objects.get(id=pk)
        self.assertEqual(signal.type_assignment.name, 'SIG')
        self.assertEqual(response_json['type']['code'], 'SIG')
        self.assertIn('created_at', response_json['type'])
        self.assertIn('created_by', response_json['type'])

        # JSONSchema validation
        new_url = response.json()['_links']['self']['href']
        response_json = self.client.get(new_url).json()
        self.assertJsonSchema(self.retrieve_signal_schema, response_json)

    @patch("signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address",
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_initial_bad_type_400(self, validate_address):
        # Create initial Signal.
        self.create_initial_data['type'] = {'code': 'GARBAGE'}

        signal_count = Signal.objects.count()
        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Signal.objects.count(), signal_count)

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

        Signal.actions.update_category_assignment({'category': new_category}, self.signal_no_image)
        self.signal_no_image.refresh_from_db()

        Signal.actions.update_category_assignment({'category': prev_category}, self.signal_no_image)
        self.signal_no_image.refresh_from_db()

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
        self.create_initial_data['source'] = 'online'
        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')

        self.assertEqual(400, response.status_code)
        self.assertEqual(response.json()['source'][0],
                         'Invalid source given for authenticated user')

    def test_validate_extra_properties_enabled(self):
        self.create_initial_data['extra_properties'] = [{
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

        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')

        self.assertEqual(201, response.status_code)
        self.assertEqual(3, Signal.objects.count())

    def test_validate_extra_properties_enabled_invalid_data(self):
        self.create_initial_data['extra_properties'] = {'old_style': 'extra_properties'}

        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')
        data = response.json()

        self.assertEqual(400, response.status_code)
        self.assertIn('extra_properties', data)
        self.assertEqual(data['extra_properties'][0], 'Invalid input.')
        self.assertEqual(2, Signal.objects.count())

    def test_missing_email_or_phone_as_empty_string(self):
        """
        For backwards compatibility: missing email or phone properties serialize as empty strings.

        Note: representation of missing values in database was changed from
        empty strings to null / None. We want to keep the REST API stable,
        hence this test. (related to SIG-1976)
        """
        detail_endpoint = self.detail_endpoint.format(pk=self.signal_with_image.id)

        # first check serialization when values are not None
        self.signal_with_image.reporter.email = 'm.elder@example.com'
        self.signal_with_image.reporter.phone = '0123456789'
        self.signal_with_image.reporter.save()

        response = self.client.get(detail_endpoint)
        response_json = response.json()
        self.assertEqual(response_json['reporter']['email'], 'm.elder@example.com')
        self.assertEqual(response_json['reporter']['phone'], '0123456789')

        # check rendering of missing email and phone:
        self.signal_with_image.reporter.email = None
        self.signal_with_image.reporter.phone = None
        self.signal_with_image.reporter.save()

        response = self.client.get(detail_endpoint)
        response_json = response.json()
        self.assertEqual(response_json['reporter']['email'], '')
        self.assertEqual(response_json['reporter']['phone'], '')

    @patch("signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address",
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_initial_no_reporter(self, validate_address):
        # Create initial Signal, check that it reached the database.
        self.create_initial_data['reporter'] = {}

        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')

        self.assertEqual(response.status_code, 201)
        response_json = response.json()

        pk = response_json['id']
        new_signal = Signal.objects.get(id=pk)
        self.assertEqual(new_signal.reporter.email, None)
        self.assertEqual(new_signal.reporter.phone, None)

    @patch("signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address",
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_initial_email_phone_empty_string(self, validate_address):
        # Create initial Signal, check that it reached the database.
        self.create_initial_data['reporter']['email'] = ''
        self.create_initial_data['reporter']['phone'] = ''

        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')

        self.assertEqual(response.status_code, 201)
        response_json = response.json()

        pk = response_json['id']
        new_signal = Signal.objects.get(id=pk)
        self.assertEqual(new_signal.reporter.email, None)
        self.assertEqual(new_signal.reporter.phone, None)

    def test_detail_endpoint_SIG_2486(self):
        """
        The date in the _display value did showed with the correct timestamp as all other dates
        """
        response = self.client.get(self.detail_endpoint.format(pk=self.signal_no_image.id))
        self.assertEqual(response.status_code, 200)

        # JSONSchema validation
        data = response.json()
        self.assertJsonSchema(self.retrieve_signal_schema, data)

        created_at = self.signal_no_image.created_at.astimezone(timezone.get_current_timezone())
        created_at_with_time_zone_str = created_at.isoformat()
        self.assertIn(created_at_with_time_zone_str, data['_display'])
        self.assertEqual(created_at_with_time_zone_str, data['created_at'])
