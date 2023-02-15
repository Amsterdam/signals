# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import os

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import include, path
from django.utils import timezone
from freezegun import freeze_time
from rest_framework.test import APITestCase

from signals.apps.signals.factories import (
    CategoryFactory,
    DepartmentFactory,
    ParentCategoryFactory,
    ServiceLevelObjectiveFactory,
    SignalFactory,
    StatusFactory
)
from signals.apps.signals.models import Signal
from signals.apps.signals.workflow import (
    AFGEHANDELD,
    AFWACHTING,
    BEHANDELING,
    GEMELD,
    VERZOEK_TOT_HEROPENEN
)

THIS_DIR = os.path.dirname(__file__)


urlpatterns = [
    path('', include('signals.apps.reporting.urls')),
]


class NameSpace:
    pass


test_urlconf = NameSpace()
test_urlconf.urlpatterns = urlpatterns


@override_settings(ROOT_URLCONF=test_urlconf)
class TestPrivateReportEndpoint(APITestCase):
    base_endpoint = '/private/reports'

    def setUp(self):
        user_model = get_user_model()
        self.superuser, _ = user_model.objects.get_or_create(
            email='signals.admin@example.com', is_superuser=True,
            defaults={'first_name': 'John', 'last_name': 'Doe', 'is_staff': True}
        )

        self.department = DepartmentFactory.create()

        parent_category = ParentCategoryFactory.create()
        self.category_1 = CategoryFactory.create(parent=parent_category, departments=[self.department])
        ServiceLevelObjectiveFactory.create(category=self.category_1, n_days=2, use_calendar_days=True)
        self.category_2 = CategoryFactory.create(parent=parent_category, departments=[self.department])
        ServiceLevelObjectiveFactory.create(category=self.category_2, n_days=3, use_calendar_days=False)
        self.category_3 = CategoryFactory.create(parent=parent_category, departments=[self.department])
        ServiceLevelObjectiveFactory.create(category=self.category_3, n_days=4, use_calendar_days=False)

    def test_signals_open_per_category_no_signals(self):
        self.client.force_authenticate(user=self.superuser)

        response = self.client.get(f'{self.base_endpoint}/signals/open')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Signal.objects.count(), 0)

        response_data = response.json()
        self.assertEqual(response_data['total_signal_count'], 0)
        self.assertEqual(len(response_data['results']), 0)

        self.client.logout()

    def test_signals_open_per_category_signals_no_filter(self):
        self.client.force_authenticate(user=self.superuser)

        with freeze_time(timezone.now() - timezone.timedelta(weeks=3)):
            SignalFactory.create_batch(5, status__state=GEMELD, category_assignment__category=self.category_1)
            SignalFactory.create_batch(3, status__state=BEHANDELING, category_assignment__category=self.category_2)
            SignalFactory.create_batch(2, status__state=AFWACHTING, category_assignment__category=self.category_3)

            # Should not show up
            SignalFactory.create_batch(5, status__state=AFGEHANDELD, category_assignment__category=self.category_1)

        self.assertEqual(Signal.objects.count(), 15)

        response = self.client.get(f'{self.base_endpoint}/signals/open')
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertEqual(response_data['total_signal_count'], 10)
        self.assertEqual(len(response_data['results']), 3)

        self.assertEqual(response_data['results'][0]['signal_count'], 5)
        self.assertEqual(response_data['results'][0]['category']['name'], self.category_1.name)
        self.assertEqual(len(response_data['results'][0]['category']['departments']), 1)
        self.assertIn(self.department.code, response_data['results'][0]['category']['departments'])

        self.assertEqual(response_data['results'][1]['signal_count'], 3)
        self.assertEqual(response_data['results'][1]['category']['name'], self.category_2.name)
        self.assertEqual(len(response_data['results'][1]['category']['departments']), 1)
        self.assertIn(self.department.code, response_data['results'][1]['category']['departments'])

        self.assertEqual(response_data['results'][2]['signal_count'], 2)
        self.assertEqual(response_data['results'][2]['category']['name'], self.category_3.name)
        self.assertEqual(len(response_data['results'][2]['category']['departments']), 1)
        self.assertIn(self.department.code, response_data['results'][2]['category']['departments'])

        self.client.logout()

    def test_signals_open_per_category_signals_filtered(self):
        self.client.force_authenticate(user=self.superuser)

        self.assertEqual(Signal.objects.count(), 0)

        start = timezone.now() - timezone.timedelta(weeks=5)
        end = timezone.now() - timezone.timedelta(weeks=3)

        response = self.client.get(f'{self.base_endpoint}/signals/open', data={'start': start, 'end': end})
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertEqual(response_data['total_signal_count'], 0)
        self.assertEqual(len(response_data['results']), 0)

        with freeze_time(timezone.now() - timezone.timedelta(weeks=4)):
            SignalFactory.create_batch(5, status__state=GEMELD, category_assignment__category=self.category_1)

            # Should not show up
            SignalFactory.create_batch(5, status__state=AFGEHANDELD, category_assignment__category=self.category_1)

        self.assertEqual(Signal.objects.count(), 10)

        response = self.client.get(f'{self.base_endpoint}/signals/open', data={'start': start, 'end': end})
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertEqual(response_data['total_signal_count'], 5)
        self.assertEqual(len(response_data['results']), 1)
        self.assertEqual(response_data['results'][0]['signal_count'], 5)
        self.assertEqual(response_data['results'][0]['category']['name'], self.category_1.name)
        self.assertEqual(len(response_data['results'][0]['category']['departments']), 1)
        self.assertIn(self.department.code, response_data['results'][0]['category']['departments'])

        self.client.logout()

    def test_signals_open_per_category_unauthorized(self):
        response = self.client.get(f'{self.base_endpoint}/signals/open')
        self.assertEqual(response.status_code, 401)

    def test_signals_reopen_requested_per_category_no_signals(self):
        self.client.force_authenticate(user=self.superuser)

        response = self.client.get(f'{self.base_endpoint}/signals/reopen-requested')
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertEqual(response_data['total_signal_count'], 0)
        self.assertEqual(len(response_data['results']), 0)

        self.client.logout()

    def test_signals_reopen_requested_per_category_no_filter(self):
        self.client.force_authenticate(user=self.superuser)

        with freeze_time(timezone.now() - timezone.timedelta(weeks=3)):
            SignalFactory.create_batch(5, status__state=GEMELD, category_assignment__category=self.category_1)
            SignalFactory.create_batch(3, status__state=BEHANDELING, category_assignment__category=self.category_2)

        with freeze_time(timezone.now() - timezone.timedelta(weeks=1)):
            for signal in Signal.objects.all():
                status = StatusFactory.create(_signal=signal, state=VERZOEK_TOT_HEROPENEN)
                signal.status = status
                signal.save()

        # Should not show up
        SignalFactory.create_batch(2, status__state=AFGEHANDELD, category_assignment__category=self.category_3)

        self.assertEqual(Signal.objects.count(), 10)

        response = self.client.get(f'{self.base_endpoint}/signals/reopen-requested')
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertEqual(response_data['total_signal_count'], 8)
        self.assertEqual(len(response_data['results']), 2)
        self.assertEqual(response_data['results'][0]['signal_count'], 5)
        self.assertEqual(response_data['results'][0]['category']['name'], self.category_1.name)
        self.assertEqual(len(response_data['results'][0]['category']['departments']), 1)
        self.assertIn(self.department.code, response_data['results'][0]['category']['departments'])

        self.assertEqual(response_data['results'][1]['signal_count'], 3)
        self.assertEqual(response_data['results'][1]['category']['name'], self.category_2.name)
        self.assertEqual(len(response_data['results'][1]['category']['departments']), 1)
        self.assertIn(self.department.code, response_data['results'][1]['category']['departments'])

        self.client.logout()

    def test_signals_reopen_requested_per_category_filtered(self):
        self.client.force_authenticate(user=self.superuser)

        with freeze_time(timezone.now() - timezone.timedelta(weeks=3)):
            SignalFactory.create_batch(5, status__state=GEMELD, category_assignment__category=self.category_1)
            SignalFactory.create_batch(3, status__state=BEHANDELING, category_assignment__category=self.category_2)

        with freeze_time(timezone.now() - timezone.timedelta(weeks=1)):
            for signal in Signal.objects.all():
                status = StatusFactory.create(_signal=signal, state=VERZOEK_TOT_HEROPENEN)
                signal.status = status
                signal.save()

        with freeze_time(timezone.now() - timezone.timedelta(weeks=12)):
            # Should not show up
            signals = SignalFactory.create_batch(2, status__state=GEMELD, category_assignment__category=self.category_3)
            for signal in signals:
                status = StatusFactory.create(_signal=signal, state=VERZOEK_TOT_HEROPENEN)
                signal.status = status
                signal.save()

        self.assertEqual(Signal.objects.count(), 10)

        start = timezone.now() - timezone.timedelta(weeks=2)
        end = timezone.now() - timezone.timedelta(days=5)

        response = self.client.get(f'{self.base_endpoint}/signals/reopen-requested', data={'start': start, 'end': end})
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertEqual(response_data['total_signal_count'], 8)
        self.assertEqual(len(response_data['results']), 2)
        self.assertEqual(response_data['results'][0]['signal_count'], 5)
        self.assertEqual(response_data['results'][0]['category']['name'], self.category_1.name)
        self.assertEqual(len(response_data['results'][0]['category']['departments']), 1)
        self.assertIn(self.department.code, response_data['results'][0]['category']['departments'])

        self.assertEqual(response_data['results'][1]['signal_count'], 3)
        self.assertEqual(response_data['results'][1]['category']['name'], self.category_2.name)
        self.assertEqual(len(response_data['results'][1]['category']['departments']), 1)
        self.assertIn(self.department.code, response_data['results'][1]['category']['departments'])

        self.client.logout()

    def test_signals_reopen_requested_per_category_unauthorized(self):
        response = self.client.get(f'{self.base_endpoint}/signals/reopen-requested')
        self.assertEqual(response.status_code, 401)
