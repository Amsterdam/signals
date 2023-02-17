# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.test import override_settings
from django.urls import include, path
from django.utils import timezone
from faker import Faker
from freezegun import freeze_time
from rest_framework.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED
from rest_framework.test import APITestCase

from signals.apps.api.views import NamespaceView
from signals.apps.my_signals.models import Token
from signals.apps.signals.factories import SignalFactory

urlpatterns = [
    path('v1/relations/', NamespaceView.as_view(), name='signal-namespace'),
    path('', include('signals.apps.my_signals.urls')),
]


class NameSpace:
    pass


test_urlconf = NameSpace()
test_urlconf.urlpatterns = urlpatterns


fake = Faker()


@override_settings(ROOT_URLCONF=test_urlconf)
class TestMySignalsLoggedInReporterEndpoint(APITestCase):
    endpoint = '/my/signals/me'

    def test_me_endpoint(self):
        for _ in range(5):
            email = fake.free_email()
            SignalFactory.create(reporter__email=email)

            token = Token.objects.create(reporter_email=email)
            request_headers = {'HTTP_AUTHORIZATION': f'Token {token.key}'}

            response = self.client.get(self.endpoint, **request_headers)

            self.assertEqual(response.status_code, HTTP_200_OK)
            self.assertEqual(response.json()['email'], email)

    def test_me_endpoint_expired_token(self):
        email = fake.free_email()

        now = timezone.now()
        with freeze_time(now - timezone.timedelta(days=7)):
            token = Token.objects.create(reporter_email=email)

        request_headers = {'HTTP_AUTHORIZATION': f'Token {token.key}'}

        response = self.client.get(self.endpoint, **request_headers)
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json()['detail'], 'Invalid token.')
