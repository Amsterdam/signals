import copy
import os
from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.test import override_settings
from django.utils import timezone
from rest_framework import status

from signals.apps.api.v1.validation.address.base import AddressValidationUnavailableException
from signals.apps.signals.factories import (
    CategoryFactory,
    ParentCategoryFactory,
    SignalFactory,
    SignalFactoryWithImage,
    SourceFactory
)
from signals.apps.signals.models import Attachment, Signal
from tests.test import SIAReadWriteUserMixin, SignalsBaseApiTestCase

THIS_DIR = os.path.dirname(__file__)
JSON_SCHEMA_DIR = os.path.join(THIS_DIR, '..', 'json_schema')


@override_settings(FEATURE_FLAGS={
    'API_SEARCH_ENABLED': False,
    'SEARCH_BUILD_INDEX': False,
    'API_DETERMINE_STADSDEEL_ENABLED': True,
    'API_FILTER_EXTRA_PROPERTIES': True,
    'API_TRANSFORM_SOURCE_BASED_ON_REPORTER': True,
    'API_TRANSFORM_SOURCE_IF_A_SIGNAL_IS_A_CHILD': True,
    'API_VALIDATE_SOURCE_AGAINST_SOURCE_MODEL': True,
    'TASK_UPDATE_CHILDREN_BASED_ON_PARENT': False,
})
class TestPrivateSignalViewSetCreate(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    endpoint = '/signals/v1/private/signals/'

    detail_json_schema_path = os.path.join(JSON_SCHEMA_DIR, 'get_signals_v1_private_signals_{pk}.json')
    signal_detail_schema = None

    def setUp(self):
        # Load the JSON Schema's
        self.signal_detail_schema = self.load_json_schema(self.detail_json_schema_path)

        parent_category = ParentCategoryFactory.create(name='main', slug='main')
        CategoryFactory.create(name='sub', slug='sub', parent=parent_category)

        for source_name in ['online', 'Interne melding', 'Telefoon – ASC']:
            SourceFactory.create(name=source_name)

        self.sia_read_write_user.user_permissions.add(Permission.objects.get(codename='sia_can_view_all_categories'))

        self.initial_post_data = dict(
            text='Mensen in het cafe maken erg veel herrie',
            location=dict(
                geometrie=dict(
                    type='point',
                    coordinates=[4.90022563, 52.36768424]
                ),
                stadsdeel="A",
                buurt_code="A04i",
                address=dict(
                    openbare_ruimte="Amstel",
                    huisnummer=1,
                    huisletter="",
                    huisnummer_toevoeging="",
                    postcode="1011PN",
                    woonplaats="Amsterdam"
                ),
                extra_properties=dict(),
            ),
            category=dict(
                category_url='/signals/v1/public/terms/categories/main/sub_categories/sub'
            ),
            reporter=dict(
                email='melder@example.com'
            ),
            incident_date_start=timezone.now().strftime('%Y-%m-%dT%H:%M'),
            source='Telefoon – ASC',
        )

    def test_create_signal_not_logged_in(self):
        self.client.logout()

        post_data = copy.deepcopy(self.initial_post_data)
        response = self.client.post(self.endpoint, post_data, format='json')
        self.assertEqual(response.status_code, 401)

    @patch('signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address')
    def test_create_initial_signal(self, validate_address):
        self.client.force_authenticate(user=self.sia_read_write_user)

        validated_address = copy.deepcopy(self.initial_post_data['location']['address'])
        validate_address.return_value = validated_address

        post_data = copy.deepcopy(self.initial_post_data)
        response = self.client.post(self.endpoint, post_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Signal.objects.count(), 1)

    @patch('signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address')
    @override_settings(API_TRANSFORM_SOURCE_BASED_ON_REPORTER_DOMAIN_EXTENSIONS='@test.com')
    @override_settings(API_TRANSFORM_SOURCE_BASED_ON_REPORTER_SOURCE='Interne melding')
    def test_create_initial_signal_transform_to_interne_melding(self, validate_address):
        self.client.force_authenticate(user=self.sia_read_write_user)

        validated_address = copy.deepcopy(self.initial_post_data['location']['address'])
        validate_address.return_value = validated_address

        post_data = copy.deepcopy(self.initial_post_data)
        post_data['reporter']['email'] = 'test-email-1@test.com'
        response = self.client.post(self.endpoint, post_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['source'], 'Interne melding')
        self.assertEqual(Signal.objects.count(), 1)
        self.assertEqual(Signal.objects.first().source, 'Interne melding')

    @override_settings(API_TRANSFORM_SOURCE_BASED_ON_REPORTER_EXCEPTIONS=('uitzondering@test.com',),
                       API_TRANSFORM_SOURCE_BASED_ON_REPORTER_DOMAIN_EXTENSIONS='@test.com')
    @patch('signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address',
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_initial_signal_interne_melding_check_exceptions(self, validate_address):
        self.client.force_authenticate(user=self.sia_read_write_user)

        validated_address = copy.deepcopy(self.initial_post_data['location']['address'])
        validate_address.return_value = validated_address

        post_data = copy.deepcopy(self.initial_post_data)
        post_data['reporter']['email'] = 'uitzondering@test.com'
        response = self.client.post(self.endpoint, post_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['source'], post_data['source'])
        self.assertEqual(Signal.objects.count(), 1)
        self.assertEqual(Signal.objects.first().source, post_data['source'])

    @patch('signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address',
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_initial_signal_invalid_source(self, validate_address):
        self.client.force_authenticate(user=self.sia_read_write_user)

        validated_address = copy.deepcopy(self.initial_post_data['location']['address'])
        validate_address.return_value = validated_address

        post_data = copy.deepcopy(self.initial_post_data)
        post_data['source'] = 'this-source-does-not-exists-so-the-create-should-fail'

        response = self.client.post(self.endpoint, post_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Signal.objects.count(), 0)

    @patch('signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address')
    @override_settings(SIGNAL_MAX_NUMBER_OF_CHILDREN=2)
    def test_create_initial_signals(self, validate_address):
        self.client.force_authenticate(user=self.sia_read_write_user)

        validated_address = copy.deepcopy(self.initial_post_data['location']['address'])
        validate_address.return_value = validated_address

        post_data = [copy.deepcopy(self.initial_post_data), copy.deepcopy(self.initial_post_data), ]
        response = self.client.post(self.endpoint, post_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Signal.objects.count(), 2)

    @patch('signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address')
    @override_settings(SIGNAL_MAX_NUMBER_OF_CHILDREN=2,
                       API_TRANSFORM_SOURCE_OF_CHILD_SIGNAL_TO='Interne melding')
    def test_create_child_signals(self, validate_address):
        self.client.force_authenticate(user=self.sia_read_write_user)

        signal = SignalFactory.create()
        self.assertEqual(Signal.objects.count(), 1)

        validated_address = copy.deepcopy(self.initial_post_data['location']['address'])
        validate_address.return_value = validated_address

        post_data = [copy.deepcopy(self.initial_post_data), copy.deepcopy(self.initial_post_data), ]
        post_data[0]['parent'] = signal.pk
        post_data[1]['parent'] = signal.pk
        post_data[1]['source'] = 'online'
        response = self.client.post(self.endpoint, post_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Signal.objects.count(), 3)
        self.assertEqual(Signal.objects.filter(parent_id__isnull=True).count(), 1)
        self.assertEqual(Signal.objects.filter(parent_id__isnull=False).count(), 2)
        self.assertEqual(Signal.objects.filter(parent_id__isnull=False)[0].source, 'Interne melding')
        self.assertEqual(Signal.objects.filter(parent_id__isnull=False)[0].source, 'Interne melding')

    @patch('signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address')
    @override_settings(SIGNAL_MAX_NUMBER_OF_CHILDREN=2)
    def test_add_child_signals(self, validate_address):
        self.client.force_authenticate(user=self.sia_read_write_user)

        signal = SignalFactory.create()
        SignalFactory.create(parent=signal)
        self.assertEqual(Signal.objects.count(), 2)

        validated_address = copy.deepcopy(self.initial_post_data['location']['address'])
        validate_address.return_value = validated_address

        post_data = [copy.deepcopy(self.initial_post_data), ]
        post_data[0]['parent'] = signal.pk
        response = self.client.post(self.endpoint, post_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Signal.objects.count(), 3)
        self.assertEqual(Signal.objects.filter(parent_id__isnull=True).count(), 1)
        self.assertEqual(Signal.objects.filter(parent_id__isnull=False).count(), 2)

    @patch('signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address')
    @override_settings(SIGNAL_MAX_NUMBER_OF_CHILDREN=1)
    def test_create_max_child_signals_exceeded(self, validate_address):
        self.client.force_authenticate(user=self.sia_read_write_user)

        signal = SignalFactory.create()
        self.assertEqual(Signal.objects.count(), 1)

        validated_address = copy.deepcopy(self.initial_post_data['location']['address'])
        validate_address.return_value = validated_address

        post_data = [copy.deepcopy(self.initial_post_data), copy.deepcopy(self.initial_post_data), ]
        post_data[0]['parent'] = signal.pk
        post_data[1]['parent'] = signal.pk
        response = self.client.post(self.endpoint, post_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Signal.objects.count(), 1)

    @patch('signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address')
    @override_settings(SIGNAL_MAX_NUMBER_OF_CHILDREN=1)
    def test_add_max_child_signals_exceeded(self, validate_address):
        self.client.force_authenticate(user=self.sia_read_write_user)

        signal = SignalFactory.create()
        SignalFactory.create(parent=signal)
        self.assertEqual(Signal.objects.count(), 2)

        validated_address = copy.deepcopy(self.initial_post_data['location']['address'])
        validate_address.return_value = validated_address

        post_data = [copy.deepcopy(self.initial_post_data), ]
        post_data[0]['parent'] = signal.pk
        response = self.client.post(self.endpoint, post_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Signal.objects.count(), 2)

    @patch('signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address')
    @override_settings(SIGNAL_MAX_NUMBER_OF_CHILDREN=3)
    def test_create_child_signals_mixed_parents_not_allowed(self, validate_address):
        self.client.force_authenticate(user=self.sia_read_write_user)

        signals = SignalFactory.create_batch(2)
        self.assertEqual(Signal.objects.count(), 2)

        validated_address = copy.deepcopy(self.initial_post_data['location']['address'])
        validate_address.return_value = validated_address

        post_data = [copy.deepcopy(self.initial_post_data), copy.deepcopy(self.initial_post_data),
                     copy.deepcopy(self.initial_post_data), ]
        post_data[0]['parent'] = signals[0].pk
        post_data[1]['parent'] = signals[1].pk
        response = self.client.post(self.endpoint, post_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Signal.objects.count(), 2)

    @patch('signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address')
    @override_settings(SIGNAL_MAX_NUMBER_OF_CHILDREN=1)
    def test_create_child_signals_child_as_parent_not_allowed(self, validate_address):
        self.client.force_authenticate(user=self.sia_read_write_user)

        parent_signal = SignalFactory.create()
        signal = SignalFactory.create(parent=parent_signal)
        self.assertEqual(Signal.objects.count(), 2)

        validated_address = copy.deepcopy(self.initial_post_data['location']['address'])
        validate_address.return_value = validated_address

        post_data = [copy.deepcopy(self.initial_post_data), ]
        post_data[0]['parent'] = signal.pk
        response = self.client.post(self.endpoint, post_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Signal.objects.count(), 2)

    @patch('signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address')
    @override_settings(SIGNAL_MAX_NUMBER_OF_CHILDREN=1)
    def test_create_child_signals_copy_attachments_from_parent(self, validate_address):
        self.client.force_authenticate(user=self.sia_read_write_user)

        signal = SignalFactoryWithImage.create()
        attachment = signal.attachments.first()
        self.assertEqual(Signal.objects.count(), 1)
        self.assertEqual(Attachment.objects.count(), 1)

        validated_address = copy.deepcopy(self.initial_post_data['location']['address'])
        validate_address.return_value = validated_address

        post_data = [copy.deepcopy(self.initial_post_data), ]
        post_data[0]['parent'] = signal.pk
        post_data[0]['attachments'] = [f'/signals/v1/private/signals/{signal.pk}/attachments/{attachment.pk}', ]
        response = self.client.post(self.endpoint, post_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Signal.objects.count(), 2)
        self.assertEqual(Signal.objects.filter(parent_id__isnull=True).count(), 1)
        self.assertEqual(Signal.objects.filter(parent_id__isnull=False).count(), 1)
        self.assertEqual(Attachment.objects.count(), 2)

    @patch('signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address')
    @override_settings(SIGNAL_MAX_NUMBER_OF_CHILDREN=1)
    def test_create_initial_and_copy_attachments_from_different_signal(self, validate_address):
        self.client.force_authenticate(user=self.sia_read_write_user)

        signal_no_image = SignalFactory.create()
        signal_with_image = SignalFactoryWithImage.create()
        attachment = signal_with_image.attachments.first()
        self.assertEqual(Signal.objects.count(), 2)
        self.assertEqual(Attachment.objects.count(), 1)

        validated_address = copy.deepcopy(self.initial_post_data['location']['address'])
        validate_address.return_value = validated_address

        post_data = copy.deepcopy(self.initial_post_data)
        post_data['parent'] = signal_no_image.pk
        post_data['attachments'] = [f'/signals/v1/private/signals/{signal_with_image.pk}/attachments/{attachment.pk}', ]
        response = self.client.post(self.endpoint, post_data, format='json')
        response_json = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response_json['attachments']), 1)
        self.assertEqual(response_json['attachments'][0], 'Attachments can only be copied from the parent Signal')

        self.assertEqual(Signal.objects.count(), 2)
        self.assertEqual(Attachment.objects.count(), 1)

    @patch("signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address")
    def test_create_initial_and_copy_attachments_not_a_child(self, validate_address):
        self.client.force_authenticate(user=self.sia_read_write_user)

        signal_with_image = SignalFactoryWithImage.create()
        attachment = signal_with_image.attachments.first()

        validated_address = copy.deepcopy(self.initial_post_data['location']['address'])
        validate_address.return_value = validated_address

        post_data = copy.deepcopy(self.initial_post_data)
        post_data['attachments'] = [f'/signals/v1/private/signals/{signal_with_image.pk}/attachments/{attachment.pk}', ]
        response = self.client.post(self.endpoint, post_data, format='json')
        response_json = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response_json['attachments']), 1)
        self.assertEqual(response_json['attachments'][0], 'Attachments can only be copied when creating a child Signal')

        self.assertEqual(Signal.objects.count(), 1)
        self.assertEqual(Attachment.objects.count(), 1)
