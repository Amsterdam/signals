# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import os
from datetime import timedelta

from django.contrib.auth.models import Permission
from django.utils import timezone
from rest_framework import status

from signals.apps.signals.factories import (
    CategoryFactory,
    DepartmentFactory,
    ParentCategoryFactory,
    SignalFactoryValidLocation,
    SourceFactory
)
from signals.apps.signals.models import Signal
from signals.test.utils import (
    SIAReadUserMixin,
    SIAReadWriteUserMixin,
    SIAWriteUserMixin,
    SignalsBaseApiTestCase
)

THIS_DIR = os.path.dirname(__file__)


class TestPrivateSignalEndpointUnAuthorized(SignalsBaseApiTestCase):
    def test_list_endpoint(self):
        response = self.client.get('/signals/experimental/private/signals/')
        self.assertEqual(response.status_code, 401)

    def test_detail_endpoint(self):
        response = self.client.get('/signals/experimental/private/signals/1')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_endpoint(self):
        response = self.client.post('/signals/experimental/private/signals/1', {})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_endpoint(self):
        response = self.client.put('/signals/experimental/private/signals/1', {})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.patch('/signals/experimental/private/signals/1', {})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_endpoint(self):
        response = self.client.delete('/signals/experimental/private/signals/1')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestPrivateSignalViewSetPermissions(SIAReadUserMixin, SIAWriteUserMixin, SIAReadWriteUserMixin,
                                          SignalsBaseApiTestCase):
    list_endpoint = '/signals/experimental/private/signals/'

    def setUp(self):
        SourceFactory.create(name='online', is_public=True, is_active=True)
        SourceFactory.create(name='test-api', is_active=True)

        self.department_1 = DepartmentFactory.create(code='TST', name='Department for testing #1', is_intern=False, )
        parent_category_1 = ParentCategoryFactory.create()
        self.subcategory_1 = CategoryFactory.create(parent=parent_category_1, departments=[self.department_1], )

        self.department_2 = DepartmentFactory.create(code='TST', name='Department for testing #1', is_intern=False, )
        parent_category_2 = ParentCategoryFactory.create()
        self.subcategory_2 = CategoryFactory.create(parent=parent_category_2, departments=[self.department_2], )

        self.signals_1 = SignalFactoryValidLocation.create_batch(5, category_assignment__category=self.subcategory_1,
                                                                 reporter=None, incident_date_start=timezone.now(),
                                                                 incident_date_end=timezone.now() + timedelta(hours=1),
                                                                 source='test-api', )

        self.signals_2 = SignalFactoryValidLocation.create_batch(5, category_assignment__category=self.subcategory_2,
                                                                 reporter=None, incident_date_start=timezone.now(),
                                                                 incident_date_end=timezone.now() + timedelta(hours=1),
                                                                 source='test-api', )

        self.sia_read_write_user.profile.departments.add(self.department_1)
        self.sia_read_user.profile.departments.add(self.department_2)

    def test_get_signals_superuser(self):
        self.client.force_authenticate(user=self.superuser)

        response = self.client.get(self.list_endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data['count'], 10)
        self.assertEqual(data['count'], Signal.objects.filter_for_user(user=self.superuser).count())
        self.assertEqual(data['count'], Signal.objects.count())
        self.assertEqual(10, Signal.objects.count())

    def test_get_signals_user_permissions_department_1(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        response = self.client.get(self.list_endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        signals_for_user_qs = Signal.objects.filter_for_user(user=self.sia_read_write_user)
        signals_not_for_user_qs = Signal.objects.exclude(
            id__in=signals_for_user_qs.values_list('id', flat=True)
        )

        data = response.json()
        self.assertEqual(data['count'], 5)
        self.assertEqual(data['count'], signals_for_user_qs.count())
        self.assertNotEqual(data['count'], Signal.objects.count())
        self.assertEqual(10, Signal.objects.count())

        for item in data['results']:
            self.assertTrue(signals_for_user_qs.filter(id=item['id']).exists())
            self.assertFalse(signals_not_for_user_qs.filter(id=item['id']).exists())

    def test_get_signals_user_permissions_department_2(self):
        self.client.force_authenticate(user=self.sia_read_user)

        response = self.client.get(self.list_endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        signals_for_user_qs = Signal.objects.filter_for_user(user=self.sia_read_user)
        signals_not_for_user_qs = Signal.objects.exclude(
            id__in=signals_for_user_qs.values_list('id', flat=True)
        )

        data = response.json()
        self.assertEqual(data['count'], 5)
        self.assertEqual(data['count'], signals_for_user_qs.count())
        self.assertNotEqual(data['count'], Signal.objects.count())
        self.assertEqual(10, Signal.objects.count())

        for item in data['results']:
            self.assertTrue(signals_for_user_qs.filter(id=item['id']).exists())
            self.assertFalse(signals_not_for_user_qs.filter(id=item['id']).exists())

    def test_get_signals_user_permissions_sia_can_view_all_categories(self):
        self.sia_read_write_user.user_permissions.add(Permission.objects.get(codename='sia_can_view_all_categories'))
        self.client.force_authenticate(user=self.sia_read_write_user)

        response = self.client.get(self.list_endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        signals_for_user_qs = Signal.objects.filter_for_user(user=self.sia_read_write_user)
        signals_not_for_user_qs = Signal.objects.exclude(
            id__in=signals_for_user_qs.values_list('id', flat=True)
        )

        data = response.json()
        self.assertEqual(data['count'], 10)
        self.assertEqual(data['count'], signals_for_user_qs.count())
        self.assertEqual(data['count'], Signal.objects.count())
        self.assertEqual(10, Signal.objects.count())
        self.assertEqual(0, signals_not_for_user_qs.count())

        for item in data['results']:
            self.assertTrue(signals_for_user_qs.filter(id=item['id']).exists())
            self.assertFalse(signals_not_for_user_qs.filter(id=item['id']).exists())
