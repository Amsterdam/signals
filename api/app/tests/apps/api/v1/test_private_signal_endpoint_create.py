import copy
import os
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import Permission
from django.test import override_settings
from django.utils import timezone
from rest_framework import status

from signals.apps.api.v1.validation.address.base import AddressValidationUnavailableException
from signals.apps.signals.models import Attachment, Signal
from tests.apps.signals.factories import (
    CategoryFactory,
    ParentCategoryFactory,
    SignalFactory,
    SignalFactoryWithImage,
    SourceFactory
)
from tests.test import SIAReadWriteUserMixin, SignalsBaseApiTestCase

THIS_DIR = os.path.dirname(__file__)


class TestPrivateSignalViewSetCreate(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    list_endpoint = '/signals/v1/private/signals/'

    def setUp(self):
        self.main_category = ParentCategoryFactory.create(name='main', slug='main')
        self.link_main_category = '/signals/v1/public/terms/categories/main'

        self.sub_category_1 = CategoryFactory.create(name='sub1', slug='sub1', parent=self.main_category)
        self.link_sub_category_1 = f'{self.link_main_category}/sub_categories/sub1'

        self.sub_category_2 = CategoryFactory.create(name='sub2', slug='sub2', parent=self.main_category)
        self.link_sub_category_2 = f'{self.link_main_category}/sub_categories/sub2'

        self.sia_read_write_user.user_permissions.add(Permission.objects.get(codename='sia_can_view_all_categories'))
        self.client.force_authenticate(user=self.sia_read_write_user)

        self.initial_data_base = dict(
            text='Mensen in het cafe maken erg veel herrie',
            location=dict(
                geometrie=dict(
                    type='point',
                    coordinates=[4.90022563, 52.36768424]
                )
            ),
            category=dict(category_url=self.link_sub_category_1),
            reporter=dict(email='melder@example.com'),
            incident_date_start=timezone.now().strftime('%Y-%m-%dT%H:%M'),
            source='Telefoon – ASC',
        )

        self.retrieve_signal_schema = self.load_json_schema(
            os.path.join(THIS_DIR, 'json_schema', 'get_signals_v1_private_signals_{pk}.json')
        )

    @patch('signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address',
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_initial_signal(self, validate_address):
        signal_count = Signal.objects.count()

        initial_data = copy.deepcopy(self.initial_data_base)
        response = self.client.post(self.list_endpoint, initial_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Signal.objects.count(), signal_count + 1)

    @patch('signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address',
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_initial_signals(self, validate_address):
        signal_count = Signal.objects.count()

        initial_data = [
            copy.deepcopy(self.initial_data_base)
            for _ in range(2)
        ]

        response = self.client.post(self.list_endpoint, initial_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Signal.objects.count(), signal_count + 2)

    @patch('signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address',
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_initial_signals_max_exceeded(self, validate_address):
        signal_count = Signal.objects.count()

        initial_data = [
            copy.deepcopy(self.initial_data_base)
            for _ in range(settings.SIGNAL_MAX_NUMBER_OF_CHILDREN + 1)
        ]

        response = self.client.post(self.list_endpoint, initial_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Signal.objects.count(), signal_count)

    @patch('signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address',
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_initial_child_signals(self, validate_address):
        parent_signal = SignalFactory.create()

        signal_count = Signal.objects.count()
        parent_signal_count = Signal.objects.filter(parent_id__isnull=True).count()
        child_signal_count = Signal.objects.filter(parent_id__isnull=False).count()

        self.assertEqual(signal_count, 1)
        self.assertEqual(parent_signal_count, 1)
        self.assertEqual(child_signal_count, 0)

        initial_data = []
        for _ in range(2):
            data = copy.deepcopy(self.initial_data_base)
            data['parent'] = parent_signal.pk
            initial_data.append(data)

        response = self.client.post(self.list_endpoint, initial_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Signal.objects.count(), signal_count + len(initial_data))
        self.assertEqual(Signal.objects.filter(parent_id__isnull=True).count(), parent_signal_count)
        self.assertEqual(Signal.objects.filter(parent_id__isnull=False).count(), len(initial_data))

    @patch('signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address',
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_initial_add_child_signals(self, validate_address):
        parent_signal = SignalFactory.create()
        SignalFactory.create(parent=parent_signal)

        signal_count = Signal.objects.count()
        parent_signal_count = Signal.objects.filter(parent_id__isnull=True).count()
        child_signal_count = Signal.objects.filter(parent_id__isnull=False).count()

        self.assertEqual(signal_count, 2)
        self.assertEqual(parent_signal_count, 1)
        self.assertEqual(child_signal_count, 1)

        initial_data = []
        for _ in range(2):
            data = copy.deepcopy(self.initial_data_base)
            data['parent'] = parent_signal.pk
            initial_data.append(data)

        response = self.client.post(self.list_endpoint, initial_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Signal.objects.count(), 4)
        self.assertEqual(Signal.objects.filter(parent_id__isnull=True).count(), 1)
        self.assertEqual(Signal.objects.filter(parent_id__isnull=False).count(), 3)

    @patch('signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address',
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_initial_child_signals_max_exceeded(self, validate_address):
        parent_signal = SignalFactory.create()
        SignalFactory.create(parent=parent_signal)
        SignalFactory.create(parent=parent_signal)

        signal_count = Signal.objects.count()
        parent_signal_count = Signal.objects.filter(parent_id__isnull=True).count()
        child_signal_count = Signal.objects.filter(parent_id__isnull=False).count()

        self.assertEqual(signal_count, 3)
        self.assertEqual(parent_signal_count, 1)
        self.assertEqual(child_signal_count, 2)

        initial_data = []
        for _ in range(2):
            data = copy.deepcopy(self.initial_data_base)
            data['parent'] = parent_signal.pk
            initial_data.append(data)

        response = self.client.post(self.list_endpoint, initial_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Signal.objects.count(), 3)
        self.assertEqual(Signal.objects.filter(parent_id__isnull=True).count(), 1)
        self.assertEqual(Signal.objects.filter(parent_id__isnull=False).count(), 2)

    @patch('signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address',
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_initial_mixed_signals_not_allowed(self, validate_address):
        parent_signal = SignalFactory.create()

        signal_count = Signal.objects.count()
        parent_signal_count = Signal.objects.filter(parent_id__isnull=True).count()
        child_signal_count = Signal.objects.filter(parent_id__isnull=False).count()

        self.assertEqual(signal_count, 1)
        self.assertEqual(parent_signal_count, 1)
        self.assertEqual(child_signal_count, 0)

        initial_data = [
            copy.deepcopy(self.initial_data_base),
            copy.deepcopy(self.initial_data_base),
        ]
        initial_data[0]['parent'] = parent_signal.pk

        response = self.client.post(self.list_endpoint, initial_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Signal.objects.count(), 1)
        self.assertEqual(Signal.objects.filter(parent_id__isnull=True).count(), 1)
        self.assertEqual(Signal.objects.filter(parent_id__isnull=False).count(), 0)

    @patch('signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address',
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_initial_child_signals_mixed_parents_not_allowed(self, validate_address):
        parent_signal_1 = SignalFactory.create()
        parent_signal_2 = SignalFactory.create()
        parent_signal_3 = SignalFactory.create()

        signal_count = Signal.objects.count()
        parent_signal_count = Signal.objects.filter(parent_id__isnull=True).count()
        child_signal_count = Signal.objects.filter(parent_id__isnull=False).count()

        self.assertEqual(signal_count, 3)
        self.assertEqual(parent_signal_count, 3)
        self.assertEqual(child_signal_count, 0)

        initial_data = [
            copy.deepcopy(self.initial_data_base),
            copy.deepcopy(self.initial_data_base),
            copy.deepcopy(self.initial_data_base),
        ]
        initial_data[0]['parent'] = parent_signal_1.pk
        initial_data[1]['parent'] = parent_signal_2.pk
        initial_data[2]['parent'] = parent_signal_3.pk

        response = self.client.post(self.list_endpoint, initial_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Signal.objects.count(), 3)
        self.assertEqual(Signal.objects.filter(parent_id__isnull=True).count(), 3)
        self.assertEqual(Signal.objects.filter(parent_id__isnull=False).count(), 0)

    @patch('signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address',
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_initial_child_signals_parent_is_child_not_allowed(self, validate_address):
        parent_signal = SignalFactory.create()
        child_signal = SignalFactory.create(parent=parent_signal)

        signal_count = Signal.objects.count()
        parent_signal_count = Signal.objects.filter(parent_id__isnull=True).count()
        child_signal_count = Signal.objects.filter(parent_id__isnull=False).count()

        self.assertEqual(signal_count, 2)
        self.assertEqual(parent_signal_count, 1)
        self.assertEqual(child_signal_count, 1)

        initial_data = [
            copy.deepcopy(self.initial_data_base),
            copy.deepcopy(self.initial_data_base),
        ]
        initial_data[0]['parent'] = child_signal.pk
        initial_data[1]['parent'] = child_signal.pk

        response = self.client.post(self.list_endpoint, initial_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Signal.objects.count(), 2)
        self.assertEqual(Signal.objects.filter(parent_id__isnull=True).count(), 1)
        self.assertEqual(Signal.objects.filter(parent_id__isnull=False).count(), 1)

    @patch('signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address',
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_initial_child_signals_copy_attachments(self, validate_address):
        parent_signal = SignalFactoryWithImage.create()

        signal_count = Signal.objects.count()
        parent_signal_count = Signal.objects.filter(parent_id__isnull=True).count()
        child_signal_count = Signal.objects.filter(parent_id__isnull=False).count()
        attachment_count = Attachment.objects.count()

        self.assertEqual(signal_count, 1)
        self.assertEqual(parent_signal_count, 1)
        self.assertEqual(child_signal_count, 0)
        self.assertEqual(attachment_count, 1)

        attachment = parent_signal.attachments.first()

        initial_data = []
        for _ in range(2):
            data = copy.deepcopy(self.initial_data_base)
            data['parent'] = parent_signal.pk
            data['attachments'] = [f'/signals/v1/private/signals/{attachment._signal_id}/attachments/{attachment.pk}', ]
            initial_data.append(data)

        response = self.client.post(self.list_endpoint, initial_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Signal.objects.count(), 3)
        self.assertEqual(Signal.objects.filter(parent_id__isnull=True).count(), 1)
        self.assertEqual(Signal.objects.filter(parent_id__isnull=False).count(), 2)
        self.assertEqual(Attachment.objects.count(), 3)

        # JSONSchema validation
        response_json = response.json()
        for response_signal in response_json:
            detail_response_json = self.client.get(response_signal['_links']['self']['href']).json()

            self.assertEqual(len(detail_response_json['attachments']), 1)
            self.assertJsonSchema(self.retrieve_signal_schema, detail_response_json)

    @patch('signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address',
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_initial_signal_interne_melding(self, validate_address):
        signal_count = Signal.objects.count()

        initial_data = copy.deepcopy(self.initial_data_base)
        initial_data['reporter']['email'] = 'test-email-1' \
                                            f'{settings.API_TRANSFORM_SOURCE_BASED_ON_REPORTER_DOMAIN_EXTENSIONS}'
        response = self.client.post(self.list_endpoint, initial_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Signal.objects.count(), signal_count + 1)

        data = response.json()
        self.assertEqual(data['source'], settings.API_TRANSFORM_SOURCE_BASED_ON_REPORTER_SOURCE)

    @override_settings(API_TRANSFORM_SOURCE_BASED_ON_REPORTER_EXCEPTIONS=('uitzondering@amsterdam.nl',))
    @patch('signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address',
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_initial_signal_interne_melding_check_exceptions(self, validate_address):
        signal_count = Signal.objects.count()

        initial_data = copy.deepcopy(self.initial_data_base)
        initial_data['reporter']['email'] = 'uitzondering@amsterdam.nl'
        response = self.client.post(self.list_endpoint, initial_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Signal.objects.count(), signal_count + 1)

        data = response.json()
        self.assertEqual(data['source'], 'Telefoon – ASC')

    @patch('signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address',
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_initial_signal_invalid_source(self, validate_address):
        signal_count = Signal.objects.count()

        SourceFactory.create_batch(5)

        initial_data = copy.deepcopy(self.initial_data_base)
        initial_data['source'] = 'this-source-does-not-exists-so-the-create-should-fail'

        with self.settings(FEATURE_FLAGS={'API_VALIDATE_SOURCE_AGAINST_SOURCE_MODEL': True}):
            response = self.client.post(self.list_endpoint, initial_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Signal.objects.count(), signal_count)

    @patch('signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address',
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_initial_signal_valid_source(self, validate_address):
        signal_count = Signal.objects.count()

        source, *_ = SourceFactory.create_batch(5)

        initial_data = copy.deepcopy(self.initial_data_base)
        initial_data['source'] = source.name

        with self.settings(FEATURE_FLAGS={'API_VALIDATE_SOURCE_AGAINST_SOURCE_MODEL': True}):
            response = self.client.post(self.list_endpoint, initial_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Signal.objects.count(), signal_count + 1)

        response_data = response.json()
        self.assertEqual(response_data['source'], source.name)

        signal = Signal.objects.get(pk=response_data['id'])
        self.assertEqual(signal.source, source.name)

    @patch('signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address',
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_child_signal_transform_source(self, validate_address):
        parent_signal = SignalFactory.create()
        signal_count = Signal.objects.count()

        source, *_ = SourceFactory.create_batch(4)
        SourceFactory.create(name=settings.API_TRANSFORM_SOURCE_BASED_ON_SIGNAL_IS_A_CHILD)

        initial_data = copy.deepcopy(self.initial_data_base)
        initial_data['source'] = source.name
        initial_data['parent'] = parent_signal.pk

        with self.settings(FEATURE_FLAGS={'API_TRANSFORM_SOURCE_IF_A_SIGNAL_IS_A_CHILD': True}):
            response = self.client.post(self.list_endpoint, initial_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Signal.objects.count(), signal_count + 1)

        response_data = response.json()
        self.assertNotEqual(response_data['source'], source.name)
        self.assertEqual(response_data['source'], settings.API_TRANSFORM_SOURCE_BASED_ON_SIGNAL_IS_A_CHILD)

        signal = Signal.objects.get(pk=response_data['id'])
        self.assertNotEqual(signal.source, source.name)
        self.assertEqual(signal.source, settings.API_TRANSFORM_SOURCE_BASED_ON_SIGNAL_IS_A_CHILD)
