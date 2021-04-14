# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from datetime import timedelta

from django.test import override_settings
from django.urls import include, path, re_path
from django.utils import timezone
from freezegun import freeze_time
from rest_framework.test import APITestCase

from signals.apps.api.views import NamespaceView, SignalContextViewSet
from signals.apps.feedback.factories import FeedbackFactory
from signals.apps.signals import workflow
from signals.apps.signals.factories import CategoryFactory, DepartmentFactory, SignalFactory
from signals.apps.signals.models import Signal
from tests.test import SIAReadWriteUserMixin, SignalsBaseApiTestCase, SuperUserMixin


class NameSpace:
    pass


urlpatterns = [
    path('', include(([
        re_path(r'v1/relations/?$',
                NamespaceView.as_view(),
                name='signal-namespace'),
        re_path(r'v1/private/signals/(?P<pk>\d+)/context/?$',
                SignalContextViewSet.as_view({'get': 'retrieve'}),
                name='private-signal-context'),
        re_path(r'v1/private/signals/(?P<pk>\d+)/context/reporter/?$',
                SignalContextViewSet.as_view({'get': 'reporter'}),
                name='private-signal-context-reporter'),
        re_path(r'v1/private/signals/(?P<pk>\d+)/context/geography/?$',
                SignalContextViewSet.as_view({'get': 'geography'}),
                name='private-signal-context-geography'),
    ], 'signals'), namespace='v1')),
]

test_urlconf = NameSpace()
test_urlconf.urlpatterns = urlpatterns


@override_settings(ROOT_URLCONF=test_urlconf)
class TestSignalContextView(SuperUserMixin, APITestCase):
    def setUp(self):
        now = timezone.now()

        self.reporter_1_email = 'reporter_1@example.com'
        self.reporter_2_email = 'reporter_2@example.com'

        with freeze_time(now - timedelta(days=5)):
            SignalFactory.create_batch(2, reporter__email=self.reporter_1_email, status__state=workflow.BEHANDELING)
            SignalFactory.create_batch(3, reporter__email=self.reporter_1_email, status__state=workflow.AFGEHANDELD)

        self.reporter_1_signals = Signal.objects.filter(reporter__email=self.reporter_1_email)

        FeedbackFactory.create(_signal=self.reporter_1_signals[0], submitted_at=now, is_satisfied=False)
        FeedbackFactory.create(_signal=self.reporter_1_signals[2], submitted_at=now, is_satisfied=False)
        FeedbackFactory.create(_signal=self.reporter_1_signals[4], submitted_at=now, is_satisfied=True)

        self.anonymous_signals = [SignalFactory.create(reporter__email=None, status__state=workflow.BEHANDELING),
                                  SignalFactory.create(reporter__email='', status__state=workflow.BEHANDELING)]
        self.reporter_2_signals = SignalFactory.create_batch(size=5, reporter__email=self.reporter_2_email)

    def test_get_signal_context(self):
        self.client.force_authenticate(user=self.superuser)

        signal_id = self.reporter_1_signals[0].pk
        response = self.client.get(f'/signals/v1/private/signals/{signal_id}/context/')
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertEqual(response_data['geography'], None)

        self.assertEqual(response_data['reporter']['signal_count'], 5)
        self.assertEqual(response_data['reporter']['open_count'], 2)
        self.assertEqual(response_data['reporter']['positive_count'], 1)
        self.assertEqual(response_data['reporter']['negative_count'], 2)

    def test_get_signal_context_reporter_detail(self):
        self.client.force_authenticate(user=self.superuser)

        signal_id = self.reporter_1_signals[1].pk
        response = self.client.get(f'/signals/v1/private/signals/{signal_id}/context/reporter/')
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertEqual(response_data['count'], 5)
        self.assertEqual(len(response_data['results']), 5)

    def test_get_signal_context_geography_detail(self):
        self.client.force_authenticate(user=self.superuser)

        signal_id = self.reporter_1_signals[2].pk
        response = self.client.get(f'/signals/v1/private/signals/{signal_id}/context/geography')
        self.assertEqual(response.status_code, 200)

    def test_get_anonymous_signals_context(self):
        self.client.force_authenticate(user=self.superuser)

        for signal in self.anonymous_signals:
            response = self.client.get(f'/signals/v1/private/signals/{signal.pk}/context/')
            self.assertEqual(response.status_code, 200)

            response_data = response.json()
            self.assertEqual(response_data['geography'], None)

            self.assertEqual(response_data['reporter'], None)

    def test_get_anonymous_signals_context_reporter_detail(self):
        self.client.force_authenticate(user=self.superuser)

        for signal in self.anonymous_signals:
            response = self.client.get(f'/signals/v1/private/signals/{signal.pk}/context/reporter/')
            self.assertEqual(response.status_code, 404)

    def test_get_anonymous_signals_context_geography_detail(self):
        self.client.force_authenticate(user=self.superuser)

        for signal in self.anonymous_signals:
            response = self.client.get(f'/signals/v1/private/signals/{signal.pk}/context/geography/')
            self.assertEqual(response.status_code, 200)


class TestSignalContextDefaultSettingsView(SuperUserMixin, APITestCase):
    """
    By default the context and reporter context detail are enabled (for now)
    The geography context is disabled until it is implemented
    """
    def setUp(self):
        self.signal = SignalFactory.create(reporter__email=None, status__state=workflow.BEHANDELING)
        self.signal_with_email = SignalFactory.create(
            reporter__email='test123@example.com', status__state=workflow.BEHANDELING)

    def test_get_signal_context(self):
        self.client.force_authenticate(user=self.superuser)

        signal_id = self.signal.pk
        response = self.client.get(f'/signals/v1/private/signals/{signal_id}/context/')
        self.assertEqual(response.status_code, 200)

    def test_get_signal_context_reporter_detail(self):
        self.client.force_authenticate(user=self.superuser)

        response = self.client.get(f'/signals/v1/private/signals/{self.signal.pk}/context/reporter/')
        self.assertEqual(response.status_code, 404)

        response = self.client.get(f'/signals/v1/private/signals/{self.signal_with_email.pk}/context/reporter/')
        self.assertEqual(response.status_code, 200)

    def test_get_signal_context_geography_detail(self):
        self.client.force_authenticate(user=self.superuser)

        signal_id = self.signal.pk
        response = self.client.get(f'/signals/v1/private/signals/{signal_id}/context/geography')
        self.assertEqual(response.status_code, 404)


class TestSignalContextPermissions(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    # Accessing SignalContext must follow the same access rules as the signals.
    # Specifically: rules around categories and departments must be followed.
    # ... but like with child signals brief information about Signals of the
    # same reporter must be available, even if those signals would not be
    # accessible.
    detail_endpoint = '/signals/v1/private/signals/{}'
    context_endpoint = '/signals/v1/private/signals/{}/context/'
    context_reporter_endpoint = '/signals/v1/private/signals/{}/context/reporter/'

    def setUp(self):
        email = 'reporter@example.com'

        self.department_yes = DepartmentFactory.create(name='department_yes')
        self.department_no = DepartmentFactory.create(name='department_no')
        self.category_yes = CategoryFactory.create(departments=[self.department_yes])
        self.category_no = CategoryFactory.create(departments=[self.department_no])
        self.signal_yes = SignalFactory.create(category_assignment__category=self.category_yes, reporter__email=email)
        self.signal_no = SignalFactory.create(category_assignment__category=self.category_no, reporter__email=email)

        self.sia_read_write_user.profile.departments.add(self.department_yes)

    def test_cannot_access_without_proper_department(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        url = self.detail_endpoint.format(self.signal_no.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        url = self.context_endpoint.format(self.signal_no.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        url = self.context_reporter_endpoint.format(self.signal_no.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_can_access_with_proper_department(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        url = self.detail_endpoint.format(self.signal_yes.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        url = self.context_endpoint.format(self.signal_yes.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        url = self.context_reporter_endpoint.format(self.signal_yes.id)
        response = self.client.get(url)
        response_json = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_json['count'], 2)

        for entry in response_json['results']:
            if entry['id'] == self.signal_yes.id:
                self.assertEqual(entry['can_view_signal'], True)
            elif entry['id'] == self.signal_no.id:
                self.assertEqual(entry['can_view_signal'], False)
