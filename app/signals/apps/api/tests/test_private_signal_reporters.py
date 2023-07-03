# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from datetime import timedelta

from django.contrib.auth.models import Permission
from django.test.utils import freeze_time
from django.utils import timezone
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_401_UNAUTHORIZED
from rest_framework.test import APITestCase

from signals.apps.signals.factories import ReporterFactory, SignalFactory
from signals.test.utils import SIAReadWriteUserMixin


class TestPrivateSignalReportersEndpointUnAuthorized(APITestCase):
    def setUp(self) -> None:
        self.signal = SignalFactory.create()

    def test_list(self) -> None:
        response = self.client.get(f'/signals/v1/private/signals/{self.signal.pk}/reporters/')
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_create(self) -> None:
        response = self.client.post(f'/signals/v1/private/signals/{self.signal.pk}/reporters/', data={})
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)


class TestPrivateSignalReportersEndpoint(SIAReadWriteUserMixin, APITestCase):
    def setUp(self) -> None:
        self.sia_read_write_user.user_permissions.add(Permission.objects.get(codename='sia_can_view_all_categories'))
        self.client.force_authenticate(user=self.sia_read_write_user)

    def test_list(self) -> None:
        signal = SignalFactory.create()

        now = timezone.now()
        for i in range(1, 5):
            with freeze_time(now + timedelta(hours=i)):
                ReporterFactory.create(_signal=signal)

        response = self.client.get(f'/signals/v1/private/signals/{signal.pk}/reporters/')
        self.assertEqual(response.status_code, HTTP_200_OK)

        response_json = response.json()
        self.assertEqual(response_json['count'], 5)
        self.assertEqual(len(response_json['results']), 5)

    def test_create(self) -> None:
        """
        TODO: Implement logic for creating a new Reporter instance.
        """
        signal = SignalFactory.create()

        response = self.client.post(f'/signals/v1/private/signals/{signal.pk}/reporters/',
                                    data={'email': 'test@example.com',
                                          'phone': '0612345678', })
        self.assertEqual(response.status_code, HTTP_201_CREATED)
