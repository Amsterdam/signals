import copy
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import Permission
from django.utils import timezone
from rest_framework import status

from signals.apps.api.v1.validation.address.base import AddressValidationUnavailableException
from signals.apps.signals.models import Signal
from tests.apps.signals.factories import CategoryFactory, ParentCategoryFactory, SignalFactory
from tests.test import SIAReadWriteUserMixin, SignalsBaseApiTestCase


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
