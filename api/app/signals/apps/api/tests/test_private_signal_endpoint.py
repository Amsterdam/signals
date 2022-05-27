# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2022 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
import copy
import json
import os
from datetime import timedelta
from unittest import skip
from unittest.mock import patch

import dateutil
from django.contrib.auth.models import Permission
from django.contrib.gis.geos import MultiPolygon, Polygon
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone
from django.utils.http import urlencode
from freezegun import freeze_time
from rest_framework import status

from signals.apps.api.validation.address.base import (
    AddressValidationUnavailableException,
    NoResultsException
)
from signals.apps.reporting.csv.utils import map_choices
from signals.apps.signals import workflow
from signals.apps.signals.factories import (
    AreaFactory,
    CategoryFactory,
    DepartmentFactory,
    ParentCategoryFactory,
    ServiceLevelObjectiveFactory,
    SignalFactory,
    SignalFactoryValidLocation,
    SignalFactoryWithImage,
    SourceFactory
)
from signals.apps.signals.factories.category_departments import CategoryDepartmentFactory
from signals.apps.signals.models import STADSDEEL_CENTRUM, Attachment, Note, Signal, SignalUser
from signals.apps.signals.tests.attachment_helpers import (
    add_image_attachments,
    add_non_image_attachments,
    small_gif
)
from signals.apps.signals.workflow import STATUS_CHOICES
from signals.test.utils import (
    SIAReadUserMixin,
    SIAReadWriteUserMixin,
    SIAWriteUserMixin,
    SignalsBaseApiTestCase
)

THIS_DIR = os.path.dirname(__file__)


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


@override_settings(FEATURE_FLAGS={
    'API_DETERMINE_STADSDEEL_ENABLED': True,
    'API_TRANSFORM_SOURCE_BASED_ON_REPORTER': True,
})
class TestPrivateSignalViewSet(SIAReadUserMixin, SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    """
    Test basic properties of the V1 /signals/v1/private/signals endpoint.

    Note: we check both the list endpoint and associated detail endpoint.
    """

    def setUp(self):
        # initialize database with 2 Signals
        self.signal_no_image = SignalFactoryValidLocation.create(user_assignment=None)
        self.signal_with_image = SignalFactoryWithImage.create(user_assignment=None)

        # No URL reversing here, these endpoints are part of the spec (and thus
        # should not change).
        self.list_endpoint = '/signals/v1/private/signals/'
        self.geo_list_endpoint = '/signals/v1/private/signals/geography'
        self.detail_endpoint = '/signals/v1/private/signals/{pk}'
        self.history_endpoint = '/signals/v1/private/signals/{pk}/history'
        self.history_image = '/signals/v1/private/signals/{pk}/image'
        self.removed_from_category_endpoint = '/signals/v1/private/signals/category/removed'

        self.subcategory = CategoryFactory.create()
        self.link_subcategory = '/signals/v1/public/terms/categories/{}/sub_categories/{}'.format(
            self.subcategory.parent.slug, self.subcategory.slug
        )

        SourceFactory.create(name='online', is_public=True, is_active=True)
        SourceFactory.create(name='valid-source', is_active=True)

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

    # -- Read tests --
    def test_list_endpoint(self):
        response = self.client.get(self.list_endpoint)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.json()['count'], 2)

        # JSONSchema validation
        data = response.json()
        self.assertJsonSchema(self.list_signals_schema, data)

    def test_geo_list_endpoint(self):
        response = self.client.get(self.geo_list_endpoint)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['features']), 2)

        # Check headers
        self.assertTrue(response.has_header('Link'))
        self.assertTrue(response.has_header('X-Total-Count'))
        self.assertEqual(response['X-Total-Count'], '2')

    def test_geo_list_endpoint_paginated(self):
        # the first page
        response = self.client.get(f'{self.geo_list_endpoint}?page_size=1')
        self.assertEqual(response.status_code, 200)

        # Check headers
        self.assertTrue(response.has_header('Link'))
        links = response['Link'].split(',')
        self.assertEqual(len(links), 2)
        self.assertIn('rel="self"', links[0])
        self.assertIn('rel="next"', links[1])
        self.assertNotIn('rel="previous"', links[1])

        self.assertTrue(response.has_header('X-Total-Count'))
        self.assertEqual(response['X-Total-Count'], '2')

        self.assertEqual(len(response.json()['features']), 1)

        # the second page
        response = self.client.get(links[1].split(';')[0][1:-1])  # The next page

        self.assertTrue(response.has_header('Link'))
        links = response['Link'].split(',')
        self.assertEqual(len(links), 2)
        self.assertIn('rel="self"', links[0])
        self.assertNotIn('rel="next"', links[1])
        self.assertIn('rel="prev"', links[1])

        self.assertTrue(response.has_header('X-Total-Count'))
        self.assertEqual(response['X-Total-Count'], '2')

        self.assertEqual(len(response.json()['features']), 1)

    @override_settings(DEBUG=True)  # we need access to the DB queries here
    @patch("signals.apps.api.views.signals.private.signals.SIGNALS_API_GEO_PAGINATE_BY", 2)
    def test_geo_list_endpoint_queries(self):
        from django.db import connection
        SignalFactory.create_batch(size=8)

        response = self.client.get(self.geo_list_endpoint + '?geopage=2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['features']), 2)

        # Check headers
        self.assertTrue(response.has_header('Link'))
        self.assertTrue(response.has_header('X-Total-Count'))
        self.assertEqual(response['X-Total-Count'], '10')

        # Confirm pagination is done in DB and not in Python
        self.assertIn('LIMIT 2 OFFSET 2', connection.queries[-1]['sql'])

        # Check the full set of Signals is not retrieved
        with connection.cursor() as cursor:
            cursor.execute(connection.queries[-1]['sql'])
            retrieved = cursor.fetchall()
        self.assertNotEqual(len(retrieved), Signal.objects.count())

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
        self.assertEqual(len(response.json()), 6)

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

    def test_history_no_permissions(self):
        """
        The sia_read_user does not have a link with any department and also is not configured with the permission
        "sia_can_view_all_categories". Therefore it should not be able to see a Signal and it's history.
        """
        self.client.logout()
        self.client.force_authenticate(user=self.sia_read_user)

        # The "sia_read_user" should not be able to get any information for this Signal
        response = self.client.get(self.detail_endpoint.format(pk=self.signal_no_image.id))
        self.assertEqual(response.status_code, 403)

        response = self.client.get(self.history_endpoint.format(pk=self.signal_no_image.id))
        self.assertEqual(response.status_code, 403)

        # Make sure the "sia_read_write_user" is logged in again for other tests
        self.client.logout()
        self.client.force_authenticate(user=self.sia_read_write_user)

    # -- write tests --

    @patch("signals.apps.api.validation.address.base.BaseAddressValidation.validate_address",
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_initial(self, validate_address):
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

        # SIG-2773
        self.assertTrue(response_json['reporter']['sharing_allowed'])

        self.assertEqual(response_json['status']['user'], self.sia_read_write_user.email)
        self.assertEqual(response_json['priority']['created_by'], self.sia_read_write_user.email)
        self.assertEqual(response_json['location']['created_by'], self.sia_read_write_user.email)
        self.assertEqual(response_json['category']['created_by'], self.sia_read_write_user.email)

    def test_create_with_status(self):
        """ Tests that an error is returned when we try to set the status """
        self.create_initial_data["status"] = {
            "state": workflow.BEHANDELING,
            "text": "Invalid stuff happening here"
        }

        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')

        self.assertEqual(400, response.status_code)

    @patch("signals.apps.api.validation.address.base.BaseAddressValidation.validate_address",
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_initial_without_stadsdeel(self, validate_address):
        # Create initial Signal, check that it reached the database.
        # This test documents Signalen Amsterdam flow as of May 2022.
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

    @override_settings(DEFAULT_SIGNAL_AREA_TYPE='district')
    @patch("signals.apps.api.validation.address.base.BaseAddressValidation.validate_address",
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_initial_assign_area(self, validate_address):
        # Create initial Signal, check that it is created and that area_name,
        # area_code, and area_type_code are set on the Location model.
        # This test documents the Signalen VNG installations' behavior.
        BBOX = [4.877157, 52.357204, 4.929686, 52.385239]
        lon = (BBOX[0] + BBOX[2]) / 2
        lat = (BBOX[1] + BBOX[3]) / 2
        geometry = MultiPolygon([Polygon.from_bbox(BBOX)], srid=4326)
        AreaFactory.create(geometry=geometry, name='Centrum', code='centrum', _type__code='district')

        signal_count = Signal.objects.count()
        create_initial_data = self.create_initial_data
        create_initial_data['location']['geometrie']['coordinates'] = [lon, lat]
        del(create_initial_data['location']['stadsdeel'])
        del(create_initial_data['location']['address'])
        del(create_initial_data['location']['buurt_code'])

        response = self.client.post(self.list_endpoint, create_initial_data, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Signal.objects.count(), signal_count + 1)

        # Check that the actions are logged with the correct user email
        new_url = response.json()['_links']['self']['href']
        response = self.client.get(new_url)
        response_json = response.json()

        # JSONSchema validation
        self.assertJsonSchema(self.retrieve_signal_schema, response_json)

        # Check that the area_name, area_code, and area_type_code fields are set correctly.
        self.assertIsNone(response_json['location']['stadsdeel'])
        self.assertEqual(response_json['location']['created_by'], self.sia_read_write_user.email)
        self.assertEqual(response_json['location']['area_type_code'], 'district')
        self.assertEqual(response_json['location']['area_code'], 'centrum')
        self.assertEqual(response_json['location']['area_name'], 'Centrum')

    @skip('Disabled for now, it no longer throws an error but logs a warning and stores the unvalidated address')
    @patch("signals.apps.api.validation.address.base.BaseAddressValidation.validate_address",
           side_effect=NoResultsException)
    def test_create_initial_invalid_location(self, validate_address):
        """ Tests that a 400 is returned when an invalid location is provided """
        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')

        self.assertEqual(response.status_code, 400)

    @patch("signals.apps.api.validation.address.base.BaseAddressValidation.validate_address")
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

    @patch("signals.apps.api.validation.address.base.BaseAddressValidation.validate_address")
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

    @patch("signals.apps.api.validation.address.base.BaseAddressValidation.validate_address",
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

    @patch("signals.apps.api.validation.address.base.BaseAddressValidation.validate_address",
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

    @patch("signals.apps.api.validation.address.base.BaseAddressValidation.validate_address",
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_initial_and_upload_image(self, validate_address):
        attachment_count = Attachment.objects.count()
        attachments_url = self.detail_endpoint.format(pk=self.signal_no_image.pk) + '/attachments/'
        note_count = Note.objects.count()

        image = SimpleUploadedFile('image.gif', small_gif, content_type='image/gif')
        response = self.client.post(attachments_url, data={'file': image})
        self.assertEqual(response.status_code, 201)

        # Check that a second upload is NOT rejected
        image2 = SimpleUploadedFile('image.gif', small_gif, content_type='image/gif')
        response = self.client.post(attachments_url, data={'file': image2})
        self.assertEqual(response.status_code, 201)

        # Check that authenticated user is stored with attachment
        self.assertEqual(Attachment.objects.count(), attachment_count + 2)
        for attachment in Attachment.objects.all().order_by('created_at')[attachment_count:]:
            self.assertEqual(self.sia_read_write_user.email, attachment.created_by)

        # Check that history contains notes that show photo's were uploaded.
        self.assertEqual(Note.objects.count(), note_count + 2)

        note_qs = Note.objects.filter(_signal=self.signal_no_image).order_by('created_at')
        attachment_qs = Attachment.objects.filter(_signal=self.signal_no_image).order_by('created_at')

        for note, attachment in zip(note_qs, attachment_qs):
            filename = os.path.basename(attachment.file.name)
            self.assertEqual(f'Bijlage toegevoegd: {filename}', note.text)
            self.assertEqual(self.sia_read_write_user.email, note.created_by)

    @patch("signals.apps.api.validation.address.base.BaseAddressValidation.validate_address",
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

    @patch("signals.apps.api.validation.address.base.BaseAddressValidation.validate_address",
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

    @patch("signals.apps.api.validation.address.base.BaseAddressValidation.validate_address",
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_initial_bad_type_400(self, validate_address):
        # Create initial Signal.
        self.create_initial_data['type'] = {'code': 'GARBAGE'}

        signal_count = Signal.objects.count()
        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Signal.objects.count(), signal_count)

    @patch("signals.apps.api.validation.address.base.BaseAddressValidation.validate_address",
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_initial_and_copy_attachments_from_parent(self, validate_address):
        signal_count = Signal.objects.count()
        attachment_count = Attachment.objects.count()

        attachment = self.signal_with_image.attachments.first()

        create_initial_data = copy.deepcopy(self.create_initial_data)
        create_initial_data['parent'] = self.signal_with_image.pk
        create_initial_data['attachments'] = [
            f'/signals/v1/private/signals/{attachment._signal_id}/attachments/{attachment.pk}',
        ]

        response = self.client.post(self.list_endpoint, create_initial_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Signal.objects.count(), signal_count + 1)
        self.assertEqual(Attachment.objects.count(), attachment_count + 1)

        # JSONSchema validation
        new_url = response.json()['_links']['self']['href']
        response_json = self.client.get(new_url).json()
        self.assertJsonSchema(self.retrieve_signal_schema, response_json)

        # Attachment for child signal is attributed to the user that creates the
        # child signals:
        for attachment in Attachment.objects.all().order_by('created_at')[attachment_count:]:
            self.assertEqual(self.sia_read_write_user.email, attachment.created_by)

    @patch("signals.apps.api.validation.address.base.BaseAddressValidation.validate_address",
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_initial_and_copy_attachments_from_different_signal(self, validate_address):
        signal_count = Signal.objects.count()
        attachment_count = Attachment.objects.count()

        attachment = self.signal_with_image.attachments.first()

        create_initial_data = copy.deepcopy(self.create_initial_data)
        create_initial_data['parent'] = self.signal_no_image.pk
        create_initial_data['attachments'] = [
            f'/signals/v1/private/signals/{attachment._signal_id}/attachments/{attachment.pk}',
        ]

        response = self.client.post(self.list_endpoint, create_initial_data, format='json')
        response_json = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response_json['attachments']), 1)
        self.assertEqual(response_json['attachments'][0], 'Attachments can only be copied from the parent Signal')

        self.assertEqual(Signal.objects.count(), signal_count)
        self.assertEqual(Attachment.objects.count(), attachment_count)

    @patch("signals.apps.api.validation.address.base.BaseAddressValidation.validate_address",
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_initial_and_copy_attachments_not_a_child(self, validate_address):
        signal_count = Signal.objects.count()
        attachment_count = Attachment.objects.count()

        attachment = self.signal_with_image.attachments.first()

        create_initial_data = copy.deepcopy(self.create_initial_data)
        if 'parent' in create_initial_data:
            del (create_initial_data['parent'])  # Make sure we are not creating a child Signal
        create_initial_data['attachments'] = [
            f'/signals/v1/private/signals/{attachment._signal_id}/attachments/{attachment.pk}',
        ]

        response = self.client.post(self.list_endpoint, create_initial_data, format='json')
        response_json = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response_json['attachments']), 1)
        self.assertEqual(response_json['attachments'][0], 'Attachments can only be copied when creating a child Signal')

        self.assertEqual(Signal.objects.count(), signal_count)
        self.assertEqual(Attachment.objects.count(), attachment_count)

    @patch("signals.apps.api.validation.address.base.BaseAddressValidation.validate_address")
    def test_update_location(self, validate_address):
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
        validate_address.return_value = validated_address

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

    @override_settings(DEFAULT_SIGNAL_AREA_TYPE='district')
    @patch("signals.apps.api.validation.address.base.BaseAddressValidation.validate_address",
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_update_location_assign_area(self, validate_address):
        # Update location check that area_name, area_code, and area_type_code
        # are set on the Location model. This test documents the Signalen VNG
        # installations' behavior.
        BBOX = [4.877157, 52.357204, 4.929686, 52.385239]
        lon = (BBOX[0] + BBOX[2]) / 2
        lat = (BBOX[1] + BBOX[3]) / 2
        geometry = MultiPolygon([Polygon.from_bbox(BBOX)], srid=4326)
        AreaFactory.create(geometry=geometry, name='Centrum', code='centrum', _type__code='district')

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
        data['location']['geometrie']['coordinates'] = [lon, lat]
        del data['location']['address']
        del data['location']['stadsdeel']
        del data['location']['buurt_code']

        # update location
        response = self.client.patch(detail_endpoint, data, format='json')
        self.assertEqual(response.status_code, 200)

        # check that there are two Locations is in the history
        response = self.client.get(history_endpoint + '?' + querystring)
        self.assertEqual(len(response.json()), 2)

        # Check that the area_name, area_code, and area_type_code fields are set correctly.
        response = self.client.get(detail_endpoint)
        response_json = response.json()
        self.assertIsNone(response_json['location']['stadsdeel'])
        self.assertEqual(response_json['location']['created_by'], self.sia_read_write_user.email)
        self.assertEqual(response_json['location']['area_type_code'], 'district')
        self.assertEqual(response_json['location']['area_code'], 'centrum')
        self.assertEqual(response_json['location']['area_name'], 'Centrum')

    @patch("signals.apps.api.validation.address.base.BaseAddressValidation.validate_address")
    def test_update_location_no_address(self, validate_address):
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
        validate_address.assert_not_called()

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

    @patch("signals.apps.api.validation.address.base.BaseAddressValidation.validate_address")
    def test_update_location_no_coordinates(self, validate_address):
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
        validate_address.assert_not_called()

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

        Signal.actions.update_category_assignment({'category': self.subcategory}, self.signal_no_image)
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

    def test_update_type(self):
        # Partial update to update the type, all interaction via API.
        detail_endpoint = self.detail_endpoint.format(pk=self.signal_no_image.id)
        history_endpoint = self.history_endpoint.format(pk=self.signal_no_image.id)

        # check that only one Type is in the history
        querystring = urlencode({'what': 'UPDATE_TYPE_ASSIGNMENT'})
        response = self.client.get(history_endpoint + '?' + querystring)
        self.assertEqual(len(response.json()), 1)

        # retrieve relevant fixture
        fixture_file = os.path.join(THIS_DIR, 'request_data', 'update_type.json')
        with open(fixture_file, 'r') as f:
            data = json.load(f)

        response = self.client.patch(detail_endpoint, data, format='json')
        self.assertEqual(response.status_code, 200)

        # check that there are two type assignments is in the history
        self.signal_no_image.refresh_from_db()
        response = self.client.get(history_endpoint + '?' + querystring)
        self.assertEqual(len(response.json()), 2)

        # check that the correct type
        self.signal_no_image.refresh_from_db()
        self.assertEqual(
            self.signal_no_image.type_assignment.name,
            'SIG'
        )

        # JSONSchema validation
        response_json = response.json()
        self.assertJsonSchema(self.list_history_schema, response_json)

    def test_update_type_bad_data_400(self):
        # Partial update to update the type, bad input data
        detail_endpoint = self.detail_endpoint.format(pk=self.signal_no_image.id)
        history_endpoint = self.history_endpoint.format(pk=self.signal_no_image.id)

        # check that only one Type is in the history
        querystring = urlencode({'what': 'UPDATE_TYPE_ASSIGNMENT'})
        response = self.client.get(history_endpoint + '?' + querystring)
        self.assertEqual(len(response.json()), 1)

        # retrieve relevant fixture
        fixture_file = os.path.join(THIS_DIR, 'request_data', 'update_type.json')
        with open(fixture_file, 'r') as f:
            data = json.load(f)
        data['type']['code'] = 'GARBAGE'

        response = self.client.patch(detail_endpoint, data, format='json')
        self.assertEqual(response.status_code, 400)

    def test_put_not_allowed(self):
        # Partial update to update the status, all interaction via API.
        detail_endpoint = self.detail_endpoint.format(pk=self.signal_no_image.id)
        response = self.client.put(detail_endpoint, {}, format='json')
        self.assertEqual(response.status_code, 405)

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

    def test_signal_promoted_to_parent(self):
        response = self.client.get(f'{self.list_endpoint}promoted/parent/', format='json')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['count'], 0)

        SignalFactory.create_batch(4)  # Should not show up inn the response because they are normal Signals

        signal = SignalFactory.create()
        SignalFactory.create(parent=signal)

        response = self.client.get(f'{self.list_endpoint}promoted/parent/', format='json')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['id'], signal.id)

    def test_signal_promoted_to_parent_after_date_x(self):
        with freeze_time(timezone.now() - timedelta(hours=24)):
            signal = SignalFactory.create()

        after = timezone.now() - timedelta(hours=12)
        response = self.client.get(f'{self.list_endpoint}promoted/parent/',
                                   data={'after': after.isoformat()},
                                   format='json')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['count'], 0)

        with freeze_time(timezone.now() - timedelta(hours=6)):
            SignalFactory.create(parent=signal)

        response = self.client.get(f'{self.list_endpoint}promoted/parent/',
                                   data={'after': after.isoformat()},
                                   format='json')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['id'], signal.id)

    def test_signal_promoted_to_parent_not_in_viewable_category_for_user(self):
        # self.sia_read_user is not a superuser, has no department or the can_view_all_categories permission
        self.client.force_authenticate(self.sia_read_user)

        with freeze_time(timezone.now() - timedelta(hours=24)):
            signal = SignalFactory.create()

        after = timezone.now() - timedelta(hours=12)
        response = self.client.get(f'{self.list_endpoint}promoted/parent/',
                                   data={'after': after.isoformat()},
                                   format='json')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['count'], 0)

        with freeze_time(timezone.now() - timedelta(hours=6)):
            SignalFactory.create(parent=signal)

        response = self.client.get(f'{self.list_endpoint}promoted/parent/',
                                   data={'after': after.isoformat()},
                                   format='json')
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

    @patch("signals.apps.api.serializers.PrivateSignalSerializerList.create")
    def test_post_django_validation_error_to_drf_validation_error(self, mock):
        mock.side_effect = ValidationError('this is a test')

        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(1, len(response.json()))
        self.assertEqual('this is a test', response.json()[0])

    @patch("signals.apps.api.serializers.PrivateSignalSerializerDetail.update")
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
        self.assertEqual(response.json()['source'][0], 'Invalid source given for authenticated user')

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
        permission = Permission.objects.get(codename='sia_can_view_contact_details')
        self.sia_read_write_user.user_permissions.add(permission)
        self.client.force_authenticate(user=self.sia_read_write_user)

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

    def test_no_permissions_to_view_contact_details(self):
        """
        SIG-4160 - [BE] Rechten op contactgegevens

        When a user has no "sia_can_view_contact_details" and there is an email and/or phone they should be rendered as
        "*****". If there is no email and/or phone they should still render as "".
        """
        detail_endpoint = self.detail_endpoint.format(pk=self.signal_with_image.id)

        self.signal_with_image.reporter.email = 'm.elder@example.com'
        self.signal_with_image.reporter.phone = '0123456789'
        self.signal_with_image.reporter.save()

        response = self.client.get(detail_endpoint)
        response_json = response.json()
        self.assertEqual(response_json['reporter']['email'], '*****')
        self.assertEqual(response_json['reporter']['phone'], '*****')

        self.signal_with_image.reporter.email = 'm.elder@example.com'
        self.signal_with_image.reporter.phone = None
        self.signal_with_image.reporter.save()

        response = self.client.get(detail_endpoint)
        response_json = response.json()
        self.assertEqual(response_json['reporter']['email'], '*****')
        self.assertEqual(response_json['reporter']['phone'], '')

        self.signal_with_image.reporter.email = None
        self.signal_with_image.reporter.phone = '0123456789'
        self.signal_with_image.reporter.save()

        response = self.client.get(detail_endpoint)
        response_json = response.json()
        self.assertEqual(response_json['reporter']['email'], '')
        self.assertEqual(response_json['reporter']['phone'], '*****')

        self.signal_with_image.reporter.email = None
        self.signal_with_image.reporter.phone = None
        self.signal_with_image.reporter.save()

        response = self.client.get(detail_endpoint)
        response_json = response.json()
        self.assertEqual(response_json['reporter']['email'], '')
        self.assertEqual(response_json['reporter']['phone'], '')

        self.signal_with_image.reporter.email = ''
        self.signal_with_image.reporter.phone = ''
        self.signal_with_image.reporter.save()

        response = self.client.get(detail_endpoint)
        response_json = response.json()
        self.assertEqual(response_json['reporter']['email'], '')
        self.assertEqual(response_json['reporter']['phone'], '')

    def test_list_no_permissions_to_view_contact_details(self):
        """
        SIG-4160 - [BE] Rechten op contactgegevens

        When a user has no "sia_can_view_contact_details" and there is an email and/or phone they should be rendered as
        "*****". If there is no email and/or phone they should still render as "".
        """
        now = timezone.now()
        with freeze_time(now + timedelta(minutes=10)):
            signal_with_email_and_phone = SignalFactoryWithImage.create()
            signal_with_email_and_phone.reporter.email = 'm.elder@example.com'
            signal_with_email_and_phone.reporter.phone = '0123456789'
            signal_with_email_and_phone.reporter.save()

        with freeze_time(now + timedelta(minutes=20)):
            signal_only_email = SignalFactoryWithImage.create()
            signal_only_email.reporter.email = 'm.elder@example.com'
            signal_only_email.reporter.phone = None
            signal_only_email.reporter.save()

        with freeze_time(now + timedelta(minutes=30)):
            signal_only_phone = SignalFactoryWithImage.create()
            signal_only_phone.reporter.email = None
            signal_only_phone.reporter.phone = '0123456789'
            signal_only_phone.reporter.save()

        with freeze_time(now + timedelta(minutes=40)):
            signal_no_email_no_phone = SignalFactoryWithImage.create()
            signal_no_email_no_phone.reporter.email = None
            signal_no_email_no_phone.reporter.phone = None
            signal_no_email_no_phone.reporter.save()

        response = self.client.get(self.list_endpoint, data={'created_after': now + timedelta(minutes=9)})
        response_json = response.json()
        self.assertEqual(response_json['count'], 4)
        self.assertEqual(len(response_json['results']), 4)

        self.assertEqual(response_json['results'][3]['reporter']['email'], '*****')
        self.assertEqual(response_json['results'][3]['reporter']['phone'], '*****')

        self.assertEqual(response_json['results'][2]['reporter']['email'], '*****')
        self.assertEqual(response_json['results'][2]['reporter']['phone'], '')

        self.assertEqual(response_json['results'][1]['reporter']['email'], '')
        self.assertEqual(response_json['results'][1]['reporter']['phone'], '*****')

        self.assertEqual(response_json['results'][0]['reporter']['email'], '')
        self.assertEqual(response_json['results'][0]['reporter']['phone'], '')

    def test_list_permissions_to_view_contact_details(self):
        """
        SIG-4160 - [BE] Rechten op contactgegevens

        When a user has the "sia_can_view_contact_details" and there is an email and/or phone they should be rendered as
        their database value or a "" if the value is None
        """
        permission = Permission.objects.get(codename='sia_can_view_contact_details')
        self.sia_read_write_user.user_permissions.add(permission)
        self.client.force_authenticate(user=self.sia_read_write_user)

        now = timezone.now()
        with freeze_time(now + timedelta(minutes=10)):
            signal_with_email_and_phone = SignalFactoryWithImage.create()
            signal_with_email_and_phone.reporter.email = 'm.elder@example.com'
            signal_with_email_and_phone.reporter.phone = '0123456789'
            signal_with_email_and_phone.reporter.save()

        with freeze_time(now + timedelta(minutes=20)):
            signal_only_email = SignalFactoryWithImage.create()
            signal_only_email.reporter.email = 'm.elder@example.com'
            signal_only_email.reporter.phone = None
            signal_only_email.reporter.save()

        with freeze_time(now + timedelta(minutes=30)):
            signal_only_phone = SignalFactoryWithImage.create()
            signal_only_phone.reporter.email = None
            signal_only_phone.reporter.phone = '0123456789'
            signal_only_phone.reporter.save()

        with freeze_time(now + timedelta(minutes=40)):
            signal_no_email_no_phone = SignalFactoryWithImage.create()
            signal_no_email_no_phone.reporter.email = None
            signal_no_email_no_phone.reporter.phone = None
            signal_no_email_no_phone.reporter.save()

        response = self.client.get(self.list_endpoint, data={'created_after': now + timedelta(minutes=9)})
        response_json = response.json()
        self.assertEqual(response_json['count'], 4)
        self.assertEqual(len(response_json['results']), 4)

        self.assertEqual(response_json['results'][3]['reporter']['email'], 'm.elder@example.com')
        self.assertEqual(response_json['results'][3]['reporter']['phone'], '0123456789')

        self.assertEqual(response_json['results'][2]['reporter']['email'], 'm.elder@example.com')
        self.assertEqual(response_json['results'][2]['reporter']['phone'], '')

        self.assertEqual(response_json['results'][1]['reporter']['email'], '')
        self.assertEqual(response_json['results'][1]['reporter']['phone'], '0123456789')

        self.assertEqual(response_json['results'][0]['reporter']['email'], '')
        self.assertEqual(response_json['results'][0]['reporter']['phone'], '')

    @patch("signals.apps.api.validation.address.base.BaseAddressValidation.validate_address",
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

    @patch("signals.apps.api.validation.address.base.BaseAddressValidation.validate_address",
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

    def test_update_directing_departments_on_parent_signal(self):
        # While the split functionality is removed from SIA/Signalen there can
        # stil be `signal.Signal` instances that were split, and still have to
        # be handled or be shown in historical data.

        parent_signal = SignalFactoryValidLocation.create(status__state=workflow.GESPLITST)

        child_signal = SignalFactoryValidLocation.create()
        child_signal.parent = parent_signal
        child_signal.save()

        department = DepartmentFactory.create()

        data = {'directing_departments': [{'id': department.pk}, ]}

        detail_endpoint = self.detail_endpoint.format(pk=parent_signal.id)
        history_endpoint = self.history_endpoint.format(pk=parent_signal.id)

        querystring = urlencode({'what': 'UPDATE_DIRECTING_DEPARTMENTS_ASSIGNMENT'})
        response = self.client.get(history_endpoint + '?' + querystring)
        self.assertEqual(len(response.json()), 0)

        # update location
        response = self.client.patch(detail_endpoint, data, format='json')
        self.assertEqual(response.status_code, 200)

        response_data = response.json()

        self.assertJsonSchema(self.retrieve_signal_schema, response_data)
        self.assertIn('directing_departments', response_data)
        self.assertEqual(len(response_data['directing_departments']), 1)
        self.assertEqual(response_data['directing_departments'][0]['id'], department.pk)
        self.assertEqual(response_data['directing_departments'][0]['code'], department.code)
        self.assertEqual(response_data['directing_departments'][0]['name'], department.name)
        self.assertEqual(response_data['directing_departments'][0]['is_intern'], department.is_intern)

        parent_signal.refresh_from_db()
        self.assertEqual(parent_signal.signal_departments.filter(relation_type='directing').count(), 1)
        self.assertIsNotNone(parent_signal.directing_departments_assignment)
        self.assertEqual(parent_signal.directing_departments_assignment.departments.count(), 1)
        self.assertEqual(parent_signal.directing_departments_assignment.departments.first().id, department.pk)

        querystring = urlencode({'what': 'UPDATE_DIRECTING_DEPARTMENTS_ASSIGNMENT'})
        response = self.client.get(history_endpoint + '?' + querystring)

        self.assertEqual(len(response.json()), 1)

    def test_deadlines_available_via_api_detail_endpoint(self):
        # self.signal has a category that has no ServiceLevelObjective associated
        # with it, so deadlines should be None
        result = self.client.get(self.detail_endpoint.format(pk=self.signal_no_image.id))
        result_json = result.json()

        deadline = result_json['category']['deadline']
        deadline_factor_3 = result_json['category']['deadline_factor_3']
        self.assertEqual(deadline, None)
        self.assertEqual(deadline_factor_3, None)

        # Create a category with ServiceLevelObjective
        cat = CategoryFactory.create()
        ServiceLevelObjectiveFactory.create(n_days=1, use_calendar_days=False, category=cat)
        signal = SignalFactory.create(category_assignment__category=cat)

        result = self.client.get(self.detail_endpoint.format(pk=signal.id))
        result_json = result.json()

        deadline = dateutil.parser.parse(result_json['category']['deadline'])
        deadline_factor_3 = dateutil.parser.parse(result_json['category']['deadline_factor_3'])
        self.assertEqual(deadline, signal.category_assignment.deadline)
        self.assertEqual(deadline_factor_3, signal.category_assignment.deadline_factor_3)

    def test_deadlines_available_via_api_list_endpoint(self):
        # self.signal has a category that has no ServiceLevelObjective associated
        # with it, so deadlines should be None
        result = self.client.get(self.list_endpoint)
        result_json = result.json()

        deadline = result_json['results'][0]['category']['deadline']
        deadline_factor_3 = result_json['results'][0]['category']['deadline_factor_3']
        self.assertEqual(deadline, None)
        self.assertEqual(deadline_factor_3, None)

        # Create a category with ServiceLevelObjective
        cat = CategoryFactory.create()
        ServiceLevelObjectiveFactory.create(n_days=1, use_calendar_days=False, category=cat)
        signal = SignalFactory.create(category_assignment__category=cat)

        result = self.client.get(self.list_endpoint)
        result_json = result.json()

        deadline = dateutil.parser.parse(result_json['results'][0]['category']['deadline'])
        deadline_factor_3 = dateutil.parser.parse(result_json['results'][0]['category']['deadline_factor_3'])
        self.assertEqual(deadline, signal.category_assignment.deadline)
        self.assertEqual(deadline_factor_3, signal.category_assignment.deadline_factor_3)


class TestPrivateSignalViewSetOrdering(SIAReadUserMixin, SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    """
    Test ordering of Signals in REST API.
    """

    def setUp(self):
        # No URL reversing here, these endpoints are part of the spec (and thus
        # should not change).
        self.list_endpoint = '/signals/v1/private/signals/'

        self.sia_read_write_user.user_permissions.add(Permission.objects.get(codename='sia_can_view_all_categories'))
        self.client.force_authenticate(user=self.sia_read_write_user)

    def _get_signal_ids(self, response_json):
        return [result['id'] for result in response_json['results']]

    def test_order_by_area_name_or_stadsdeel(self):
        # Sort by area_name, add the ,id to the ordering query parameter to make
        # the order of None values predictable. Default behavior of Postgres is
        # to sort NULLS LAST for ascending order en NULLS FIRST for descending.
        # This test also checks that area_name and stadsdeel ordering behave
        # the same.
        signal_a = SignalFactoryValidLocation.create(location__area_name='a')
        signal_a.location.stadsdeel = 'a'  # factory overwrites this property post generation
        signal_a.location.save()
        signal_A = SignalFactoryValidLocation.create(location__area_name='A')
        signal_A.location.stadsdeel = 'A'
        signal_A.location.save()
        signal_B = SignalFactoryValidLocation.create(location__area_name='B')
        signal_B.location.stadsdeel = 'B'
        signal_B.location.save()

        signal_none1 = SignalFactoryValidLocation.create(location__area_name=None)
        signal_none1.location.stadsdeel = None
        signal_none1.location.save()
        signal_none2 = SignalFactoryValidLocation.create(location__area_name=None)
        signal_none2.location.stadsdeel = None
        signal_none2.location.save()

        # ascending (add the ,id to order Nones predictably)
        response = self.client.get(f'{self.list_endpoint}?ordering=area_name,id')
        self.assertEqual(response.status_code, 200)
        signal_ids_area_name_asc = self._get_signal_ids(response.json())

        response = self.client.get(f'{self.list_endpoint}?ordering=stadsdeel,id')
        self.assertEqual(response.status_code, 200)
        signal_ids_stadsdeel_asc = self._get_signal_ids(response.json())

        self.assertEqual(
            signal_ids_area_name_asc, [signal_a.id, signal_A.id, signal_B.id, signal_none1.id, signal_none2.id])
        self.assertEqual(signal_ids_area_name_asc, signal_ids_stadsdeel_asc)

        # descending
        response = self.client.get(f'{self.list_endpoint}?ordering=-area_name,-id')
        self.assertEqual(response.status_code, 200)
        signal_ids_area_name_desc = self._get_signal_ids(response.json())

        response = self.client.get(f'{self.list_endpoint}?ordering=-stadsdeel,-id')
        self.assertEqual(response.status_code, 200)
        signal_ids_stadsdeel_desc = self._get_signal_ids(response.json())

        self.assertEqual(
            signal_ids_area_name_desc, [signal_none2.id, signal_none1.id, signal_B.id, signal_A.id, signal_a.id])
        self.assertEqual(signal_ids_area_name_desc, signal_ids_stadsdeel_desc)

    def test_order_by_created_at_or_updated_at(self):
        now = timezone.now()
        with freeze_time(now - timedelta(hours=3)):
            signal_1 = SignalFactoryValidLocation.create()
        with freeze_time(now - timedelta(hours=2)):
            signal_2 = SignalFactoryValidLocation.create()
        with freeze_time(now - timedelta(hours=1)):
            signal_3 = SignalFactoryValidLocation.create()

        # ascending
        response = self.client.get(f'{self.list_endpoint}?ordering=created_at')
        self.assertEqual(response.status_code, 200)
        signal_ids_created_at_asc = self._get_signal_ids(response.json())

        response = self.client.get(f'{self.list_endpoint}?ordering=updated_at')
        self.assertEqual(response.status_code, 200)
        signal_ids_updated_at_asc = self._get_signal_ids(response.json())

        self.assertEqual(signal_ids_created_at_asc, [signal_1.id, signal_2.id, signal_3.id])
        self.assertEqual(signal_ids_created_at_asc, signal_ids_updated_at_asc)

        # descending
        response = self.client.get(f'{self.list_endpoint}?ordering=-created_at')
        self.assertEqual(response.status_code, 200)
        signal_ids_created_at_desc = self._get_signal_ids(response.json())

        response = self.client.get(f'{self.list_endpoint}?ordering=-updated_at')
        self.assertEqual(response.status_code, 200)
        signal_ids_updated_at_desc = self._get_signal_ids(response.json())

        self.assertEqual(signal_ids_created_at_desc, [signal_3.id, signal_2.id, signal_1.id])
        self.assertEqual(signal_ids_created_at_desc, signal_ids_updated_at_desc)

    def test_order_by_status(self):
        # Document ordering behavior with respect to state. Current behavior is
        # to sort by code and not by human readable text - this mismatch means
        # that to a user the Signal instances do not appear to be sorted
        # alphabetically. (We sort on state, user sees state_display.)
        for code, _ in STATUS_CHOICES:
            SignalFactoryValidLocation.create(status__state=code)

        # sort ascending
        response = self.client.get(f'{self.list_endpoint}?ordering=status')
        self.assertEqual(response.status_code, 200)

        response_state_displays = []
        response_states = []
        for result in response.json()['results']:
            response_state_displays.append(result['status']['state_display'])
            response_states.append(result['status']['state'])

        # States are sorted correctly, state_displays are not. We use the DB to
        # get ordered lists because the endpoint uses the DB to do ordering and
        # Python list sort behaves differently when strings contain special
        # characters like a space.
        ordered_states = list(Signal.objects.all().order_by('status__state').values_list('status__state', flat=True))
        ordered_state_displays = list(
            Signal.objects.all()
            .annotate(state_display=map_choices('status__state', STATUS_CHOICES))
            .order_by('state_display')
            .values_list('state_display', flat=True)
        )

        self.assertEqual(ordered_states, response_states)
        # REST API users do not get properly sorted state displays:
        self.assertNotEqual(ordered_state_displays, response_state_displays)


@override_settings(FEATURE_FLAGS={
    'API_DETERMINE_STADSDEEL_ENABLED': True,
    'API_TRANSFORM_SOURCE_BASED_ON_REPORTER': True,
})
class TestPrivateSignalAttachments(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    list_endpoint = '/signals/v1/private/signals/'
    detail_endpoint = list_endpoint + '{}'
    attachment_endpoint = detail_endpoint + '/attachments/'
    test_host = 'http://testserver'

    def setUp(self):
        SourceFactory.create(name='valid-source')
        self.signal = SignalFactory.create()

        fixture_file = os.path.join(THIS_DIR, 'request_data', 'create_initial.json')
        with open(fixture_file, 'r') as f:
            self.create_initial_data = json.load(f)
        self.create_initial_data['source'] = 'valid-source'

        self.sia_read_write_user.user_permissions.add(Permission.objects.get(codename='sia_can_view_all_categories'))
        self.client.force_authenticate(user=self.sia_read_write_user)

    def test_image_upload(self):
        endpoint = self.attachment_endpoint.format(self.signal.id)
        image = SimpleUploadedFile('image.gif', small_gif, content_type='image/gif')

        response = self.client.post(endpoint, data={'file': image})

        self.assertEqual(response.status_code, 201)
        self.assertIsInstance(self.signal.attachments.first(), Attachment)
        self.assertIsInstance(self.signal.attachments.filter(is_image=True).first(), Attachment)

    def test_created_by_field_present(self):
        # We must expose the username of the user who uploaded an attachment.
        endpoint = self.attachment_endpoint.format(self.signal.id)
        image = SimpleUploadedFile('image.gif', small_gif, content_type='image/gif')

        response = self.client.post(endpoint, data={'file': image})

        self.assertEqual(response.status_code, 201)
        response_json = response.json()
        self.assertEqual(response_json['created_by'], self.sia_read_write_user.email)

    def test_attachment_upload_extension_not_allowed(self):
        endpoint = self.attachment_endpoint.format(self.signal.id)
        doc_upload = os.path.join(THIS_DIR, 'test-data', 'sia-ontwerp-testfile.doc')

        with open(doc_upload, encoding='latin-1') as f:
            data = {"file": f}

            response = self.client.post(endpoint, data)

        self.assertEqual(response.status_code, 400)

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
@override_settings(FEATURE_FLAGS={
    'API_DETERMINE_STADSDEEL_ENABLED': True,
    'API_TRANSFORM_SOURCE_BASED_ON_REPORTER': True,
})
class TestPrivateSignalViewSetPermissions(SIAReadUserMixin, SIAWriteUserMixin, SIAReadWriteUserMixin,
                                          SignalsBaseApiTestCase):
    list_endpoint = '/signals/v1/private/signals/'
    detail_endpoint = '/signals/v1/private/signals/{pk}'
    history_endpoint = '/signals/v1/private/signals/{pk}/history'

    category_url_pattern = '/signals/v1/public/terms/categories/{}'
    subcategory_url_pattern = '/signals/v1/public/terms/categories/{}/sub_categories/{}'

    def setUp(self):
        SourceFactory.create(name='online', is_public=True, is_active=True)
        SourceFactory.create(name='test-api', is_active=True)

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

        self.sia_read_write_user.profile.departments.add(self.department)

    def test_get_endpoints(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        endpoints = (
            self.list_endpoint,
            self.detail_endpoint.format(pk=self.signal.pk),
            self.history_endpoint.format(pk=self.signal.pk),
        )

        for endpoint in endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 200, msg='{}'.format(endpoint))

    def test_create_initial_forbidden(self):
        self.client.force_authenticate(user=self.sia_read_user)

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
        self.client.force_authenticate(user=self.sia_read_write_user)

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
        self.client.force_authenticate(user=self.sia_read_user)

        detail_endpoint = self.detail_endpoint.format(pk=self.signal.id)
        data = {'notes': [{'text': 'This is a text for a note.'}]}
        response = self.client.patch(detail_endpoint, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_note(self):
        self.assertEqual(self.signal.notes.count(), 0)

        self.client.force_authenticate(user=self.sia_read_write_user)

        detail_endpoint = self.detail_endpoint.format(pk=self.signal.id)
        data = {'notes': [{'text': 'This is a text for a note.'}]}
        response = self.client.patch(detail_endpoint, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.signal.refresh_from_db()

        self.assertEqual(self.signal.notes.count(), 1)
        self.assertEqual(self.signal.notes.first().created_by, self.sia_read_write_user.email)

    def test_change_status_forbidden(self):
        self.client.force_authenticate(user=self.sia_read_user)

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
        self.client.force_authenticate(user=self.sia_read_write_user)

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
        self.assertEqual(self.signal.status.user, self.sia_read_write_user.email)

    def test_change_category_forbidden(self):
        self.client.force_authenticate(user=self.sia_read_user)

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

        self.client.force_authenticate(user=self.sia_read_write_user)

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
        self.assertEqual(self.signal.category_assignment.created_by, self.sia_read_write_user.email)

    @patch('signals.apps.api.validation.address.base.BaseAddressValidation.validate_address')
    def test_update_location(self, validate_address):
        self.client.force_authenticate(user=self.sia_read_write_user)

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
        validate_address.return_value = validated_address

        response = self.client.patch(detail_endpoint, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.signal.refresh_from_db()

        self.assertEqual(self.signal.location.created_by, self.sia_read_write_user.email)

    def test_create_initial_role_based_permission(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

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
        self.client.force_authenticate(user=self.sia_read_write_user)

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

        self.client.force_authenticate(user=self.sia_read_write_user)

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
        self.client.force_authenticate(user=self.sia_read_write_user)

        response = self.client.get(self.list_endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['count'], Signal.objects.filter_for_user(user=self.sia_read_write_user).count())
        self.assertNotEqual(data['count'], Signal.objects.count())
        self.assertEqual(2, Signal.objects.count())

    def test_change_category_to_other_category_in_other_department(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        response = self.client.get(self.list_endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['count'], Signal.objects.filter_for_user(user=self.sia_read_write_user).count())
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
        self.assertEqual(data['count'], Signal.objects.filter_for_user(user=self.sia_read_write_user).count())
        self.assertNotEqual(data['count'], Signal.objects.count())
        self.assertEqual(2, Signal.objects.count())

    def test_get_signal_not_my_department(self):
        self.client.force_authenticate(user=self.sia_read_write_user)
        detail_endpoint = self.detail_endpoint.format(pk=self.signal_2.id)
        response = self.client.get(detail_endpoint)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_change_signal_not_my_department(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        data = {
            'category': {
                'text': 'Update category test',
                'sub_category': self.link_subcategory_2
            }
        }

        detail_endpoint = self.detail_endpoint.format(pk=self.signal_2.id)
        response = self.client.patch(detail_endpoint, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_not_allowed_via_api(self):
        # Signals are allowed to be deleted at the database level, but until it
        # is known what requirements / restrictions are at REST API level we do
        # not allow deletes via REST API.
        self.client.force_authenticate(user=self.superuser)
        detail_endpoint = self.detail_endpoint.format(pk=self.signal_2.id)
        response = self.client.delete(detail_endpoint)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class TestSignalChildrenEndpoint(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    def setUp(self):
        self.child_endpoint = '/signals/v1/private/signals/{pk}/children/'
        self.detail_endpoint = '/signals/v1/private/signals/{pk}'

        # test signals
        self.parent_signal = SignalFactory.create()
        self.child_signal = SignalFactory.create(parent=self.parent_signal)
        self.normal_signal = SignalFactory.create()

    def test_shows_children(self):
        # Check that we can access a parent signal's children.
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(self.child_endpoint.format(pk=self.parent_signal.pk))
        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        self.assertEqual(response_json['count'], 1)
        self.assertEqual(response_json['results'][0]['id'], self.child_signal.pk)

        # Check that accessing child endpoint on child signal results in 404
        response = self.client.get(self.child_endpoint.format(pk=self.child_signal.pk))
        self.assertEqual(response.status_code, 404)

        # Check that accessing child endpoint on normal signal results in 404
        self.assertFalse(self.normal_signal.is_parent)
        response = self.client.get(self.child_endpoint.format(pk=self.normal_signal.pk))
        self.assertEqual(response.status_code, 404)

    def test_only_for_visible_parent(self):
        self.client.force_authenticate(user=self.sia_read_write_user)
        response = self.client.get(self.detail_endpoint.format(pk=self.parent_signal.pk))
        self.assertEqual(response.status_code, 403)

        response = self.client.get(self.child_endpoint.format(pk=self.parent_signal.pk))
        self.assertEqual(response.status_code, 403)

    def test_shows_children_can_view_all_children_true_superuser(self):
        """
        If a SuperUser access the children endpoint the "can_view_signal" should all be True
        """
        self.client.force_authenticate(user=self.superuser)

        parent_signal = SignalFactory.create()
        children = SignalFactory.create_batch(2, parent=parent_signal)

        response = self.client.get(self.child_endpoint.format(pk=parent_signal.pk))
        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        self.assertEqual(response_json['count'], len(children))
        self.assertTrue(response_json['results'][0]['can_view_signal'])
        self.assertTrue(response_json['results'][1]['can_view_signal'])

    def test_shows_children_can_view_all_children_true_permission_can_view_all_categories(self):
        """
        If a User with the special "sia_can_view_all_categories" permission access the children endpoint
        the "can_view_signal" should all be True
        """
        self.sia_read_write_user.user_permissions.add(Permission.objects.get(codename='sia_can_view_all_categories'))
        self.client.force_authenticate(user=self.sia_read_write_user)

        parent_signal = SignalFactory.create()
        SignalFactory.create_batch(2, parent=parent_signal)

        response = self.client.get(self.child_endpoint.format(pk=parent_signal.pk))
        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        self.assertEqual(response_json['count'], 2)
        self.assertTrue(response_json['results'][0]['can_view_signal'])
        self.assertTrue(response_json['results'][1]['can_view_signal'])

    def test_shows_children_can_view_all_children_true(self):
        """
        User has permissions to view all Signals in certain categories, and all children belong to one of those
        categories, then the "can_view_signal" should all be True
        """
        parent_category = ParentCategoryFactory.create()
        child_category_1 = CategoryFactory.create(parent=parent_category)
        child_category_2 = CategoryFactory.create(parent=parent_category)

        department = DepartmentFactory.create()

        CategoryDepartmentFactory.create(category=child_category_1, department=department, can_view=True)
        CategoryDepartmentFactory.create(category=child_category_2, department=department, can_view=True)

        self.sia_read_write_user.profile.departments.add(department)
        self.client.force_authenticate(user=self.sia_read_write_user)

        parent_signal = SignalFactory.create(category_assignment__category=child_category_1)
        SignalFactory.create(parent=parent_signal, category_assignment__category=child_category_1)
        SignalFactory.create(parent=parent_signal, category_assignment__category=child_category_2)

        response = self.client.get(self.child_endpoint.format(pk=parent_signal.pk))
        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        self.assertEqual(response_json['count'], 2)
        self.assertTrue(response_json['results'][0]['can_view_signal'])
        self.assertTrue(response_json['results'][1]['can_view_signal'])

    def test_shows_children_can_view_all_children_false(self):
        """
        User has no permissions to view all Signals in certain categories, and all children belong to one of those
        categories, then the "can_view_signal" should all be False
        """
        parent_category = ParentCategoryFactory.create()
        child_category_1 = CategoryFactory.create(parent=parent_category)
        child_category_2 = CategoryFactory.create(parent=parent_category)

        department = DepartmentFactory.create()
        CategoryDepartmentFactory.create(category=child_category_1, department=department, can_view=True)

        self.sia_read_write_user.profile.departments.add(department)
        self.client.force_authenticate(user=self.sia_read_write_user)

        parent_signal = SignalFactory.create(category_assignment__category=child_category_1)
        SignalFactory.create_batch(2, parent=parent_signal, category_assignment__category=child_category_2)

        response = self.client.get(self.child_endpoint.format(pk=parent_signal.pk))
        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        self.assertEqual(response_json['count'], 2)
        self.assertFalse(response_json['results'][0]['can_view_signal'])
        self.assertFalse(response_json['results'][1]['can_view_signal'])

    def test_shows_children_can_view_all_children_mixed(self):
        """
        User has permissions to view all Signals in certain categories, and some children belong to one of those
        categories, then the "can_view_signal" should all be mixed (True and False)
        """
        parent_category = ParentCategoryFactory.create()
        child_category_1 = CategoryFactory.create(parent=parent_category)
        child_category_2 = CategoryFactory.create(parent=parent_category)

        department = DepartmentFactory.create()

        CategoryDepartmentFactory.create(category=child_category_1, department=department, can_view=True)

        self.sia_read_write_user.profile.departments.add(department)
        self.client.force_authenticate(user=self.sia_read_write_user)

        parent_signal = SignalFactory.create(category_assignment__category=child_category_1)
        child_1 = SignalFactory.create(parent=parent_signal, category_assignment__category=child_category_1)
        SignalFactory.create(parent=parent_signal, category_assignment__category=child_category_2)

        response = self.client.get(self.child_endpoint.format(pk=parent_signal.pk))
        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        self.assertEqual(response_json['count'], 2)

        for item in response_json['results']:
            if item['id'] == child_1.id:
                # The currently logged in User should have permissions to view first child
                self.assertTrue(item['can_view_signal'])
            else:
                # The currently logged in User should NOT have permissions to view the second child
                self.assertFalse(item['can_view_signal'])


class TestSignalEndpointRouting(SIAReadWriteUserMixin, SIAReadUserMixin, SignalsBaseApiTestCase):
    def setUp(self):
        self.list_endpoint = '/signals/v1/private/signals/'
        self.detail_endpoint = '/signals/v1/private/signals/{pk}'
        self.history_endpoint = '/signals/v1/private/signals/{pk}/history'
        self.subcategory_url_pattern = '/signals/v1/public/terms/categories/{}/sub_categories/{}'
        self.sia_read_write_user.user_permissions.add(Permission.objects.get(codename='sia_can_view_all_categories'))

        # test signals
        self.signal = SignalFactory.create(user_assignment=None)
        self.department = DepartmentFactory.create()
        self.category = CategoryFactory.create()

    def test_routing_add_remove(self):
        self.client.force_authenticate(user=self.sia_read_write_user)
        detail_endpoint = self.detail_endpoint.format(pk=self.signal.id)
        data = {
            'routing_departments': [
                {
                    'id': self.department.id
                }
            ]
        }
        response = self.client.patch(detail_endpoint, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.signal.refresh_from_db()
        self.assertEqual(self.signal.routing_assignment.departments.count(), 1)

        # remove routing
        data = {
            'routing_departments': []
        }
        response = self.client.patch(detail_endpoint, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.signal.refresh_from_db()
        self.assertEqual(self.signal.routing_assignment.departments.count(), 0)

    def test_routing_user_add_remove(self):
        self.client.force_authenticate(user=self.sia_read_write_user)
        detail_endpoint = self.detail_endpoint.format(pk=self.signal.id)
        data = {
            'routing_departments': [
                {
                    'id': self.department.id
                }
            ]
        }
        response = self.client.patch(detail_endpoint, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.signal.refresh_from_db()

        data = {
            'assigned_user_email': self.sia_read_write_user.email
        }
        response = self.client.patch(detail_endpoint, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.signal.refresh_from_db()
        self.assertEqual(self.signal.user_assignment.user.id, self.sia_read_write_user.id)

        # remove user assignment
        data = {
            'assigned_user_email': None
        }
        response = self.client.patch(detail_endpoint, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.signal.refresh_from_db()
        self.assertEqual(self.signal.user_assignment.user, None)

    def test_routing_add_and_check_user(self):
        self.client.force_authenticate(user=self.sia_read_write_user)
        read_client = self.client_class()
        read_client.force_authenticate(user=self.sia_read_user)

        response = read_client.get(self.list_endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['count'], 0)

        response = read_client.get(self.detail_endpoint.format(pk=self.signal.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        detail_endpoint = self.detail_endpoint.format(pk=self.signal.id)
        data = {
            'routing_departments': [
                {
                    'id': self.department.id
                }
            ]
        }
        response = self.client.patch(detail_endpoint, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.signal.refresh_from_db()

        # add user to department
        self.sia_read_user.profile.departments.add(self.department)

        response = read_client.get(self.list_endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['count'], 1)

        response = read_client.get(self.detail_endpoint.format(pk=self.signal.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_routing_remove_and_check_user(self):
        # adds routing to signal, add user (from dept)
        # change to another department -> user should be removed
        self.client.force_authenticate(user=self.sia_read_write_user)

        detail_endpoint = self.detail_endpoint.format(pk=self.signal.id)
        data = {
            'routing_departments': [
                {
                    'id': self.department.id
                }
            ]
        }
        response = self.client.patch(detail_endpoint, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.signal.refresh_from_db()

        # add user to department
        self.sia_read_user.profile.departments.add(self.department)

        # assign user
        data = {
            'assigned_user_email': self.sia_read_write_user.email
        }
        response = self.client.patch(detail_endpoint, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['assigned_user_email'], self.sia_read_write_user.email)

        new_department = DepartmentFactory.create()
        data = {
            'routing_departments': [
                {
                    'id': new_department.id
                }
            ]
        }
        response = self.client.patch(detail_endpoint, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIsNone(data['assigned_user_email'])

        self.signal.refresh_from_db()
        self.assertEqual(self.signal.user_assignment, None)

    def test_routing_change_category_and_check_user_and_routing(self):
        # adds routing to signal, add user (from dept)
        # change category assignment -> user, routing assignment should be removed
        self.client.force_authenticate(user=self.sia_read_write_user)

        detail_endpoint = self.detail_endpoint.format(pk=self.signal.id)
        data = {
            'routing_departments': [
                {
                    'id': self.department.id
                }
            ]
        }
        response = self.client.patch(detail_endpoint, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.signal.refresh_from_db()

        # add user to department
        self.sia_read_user.profile.departments.add(self.department)

        new_parentcategory = ParentCategoryFactory.create()
        new_subcategory = CategoryFactory.create(
            parent=new_parentcategory,
            departments=[self.department],
        )

        link_subcategory = self.subcategory_url_pattern.format(
            new_parentcategory.slug, new_subcategory.slug
        )

        data = {
            'category': {
                'text': 'change cat test',
                'category_url': link_subcategory
            }
        }
        response = self.client.patch(detail_endpoint, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIsNone(data['assigned_user_email'])

        self.signal.refresh_from_db()
        self.assertEqual(self.signal.user_assignment, None)
        self.assertEqual(self.signal.routing_assignment, None)

    def test_history_of_user_assignment(self):
        # VNG issue: https://github.com/Signalen/product-steering/issues/136
        # Setting a user and then removing a user should remain visible in
        # the Signal's history.
        detail_endpoint = self.detail_endpoint.format(pk=self.signal.id)
        history_endpoint = self.history_endpoint.format(pk=self.signal.id)
        self.client.force_authenticate(user=self.sia_read_write_user)

        signal_user_count = SignalUser.objects.count()

        # set assigned user to a user
        data = {'assigned_user_email': self.sia_read_write_user.email}
        response = self.client.patch(detail_endpoint, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = response.json()
        self.assertEqual(response_json['assigned_user_email'], self.sia_read_write_user.email)

        response = self.client.get(history_endpoint + '?what=UPDATE_USER_ASSIGNMENT')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = response.json()
        self.assertEqual(len(response_json), 1)  # one user assignment in history
        self.assertEqual(
            response_json[0]['action'], f'Melding toewijzing gewijzigd naar: {self.sia_read_write_user.email}')
        self.assertEqual(response_json[0]['who'], self.sia_read_write_user.email)

        self.assertEqual(SignalUser.objects.count(), signal_user_count + 1)

        # remove assigned user by setting it to None
        data = {'assigned_user_email': None}
        response = self.client.patch(detail_endpoint, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = response.json()
        self.assertEqual(response_json['assigned_user_email'], None)

        response = self.client.get(history_endpoint + '?what=UPDATE_USER_ASSIGNMENT')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = response.json()
        self.assertEqual(len(response_json), 2)  # two user assignments in history
        self.assertEqual(response_json[0]['action'], 'Melding niet meer toegewezen aan behandelaar.')
        self.assertEqual(response_json[0]['who'], self.sia_read_write_user.email)

        self.assertEqual(SignalUser.objects.count(), signal_user_count + 2)

        # again set assigned user to a user
        data = {'assigned_user_email': self.sia_read_write_user.email}
        response = self.client.patch(detail_endpoint, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = response.json()
        self.assertEqual(response_json['assigned_user_email'], self.sia_read_write_user.email)

        response = self.client.get(history_endpoint + '?what=UPDATE_USER_ASSIGNMENT')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = response.json()
        self.assertEqual(len(response_json), 3)  # three user assignments in history
        self.assertEqual(
            response_json[0]['action'], f'Melding toewijzing gewijzigd naar: {self.sia_read_write_user.email}')
        self.assertEqual(response_json[0]['who'], self.sia_read_write_user.email)

        self.assertEqual(SignalUser.objects.count(), signal_user_count + 3)
