# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from datetime import timedelta
from unittest import skip

from django.contrib.gis.geos import Point
from django.db.models import Q
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
from tests.apps.signals.valid_locations import ARENA, BLAUWE_THEEHUIS, FILMMUSEUM_EYE, STADHUIS
from tests.test import SIAReadWriteUserMixin, SignalsBaseApiTestCase, SuperUserMixin


class NameSpace:
    pass


urlpatterns = [
    path('', include([
        re_path(r'v1/relations/?$',
                NamespaceView.as_view(),
                name='signal-namespace'),
        re_path(r'v1/private/signals/(?P<pk>\d+)/context/?$',
                SignalContextViewSet.as_view({'get': 'retrieve'}),
                name='private-signal-context'),
        re_path(r'v1/private/signals/(?P<pk>\d+)/context/reporter/?$',
                SignalContextViewSet.as_view({'get': 'reporter'}),
                name='private-signal-context-reporter'),
        re_path(r'v1/private/signals/(?P<pk>\d+)/context/near/geography/?$',
                SignalContextViewSet.as_view({'get': 'near'}),
                name='private-signal-context-near-geography'),
    ])),
]

test_urlconf = NameSpace()
test_urlconf.urlpatterns = urlpatterns


@override_settings(ROOT_URLCONF=test_urlconf)
class TestSignalContextView(SuperUserMixin, APITestCase):
    def setUp(self):
        now = timezone.now()

        self.reporter_1_email = 'reporter_1@example.com'
        self.reporter_2_email = 'reporter_2@example.com'

        self.test_category = CategoryFactory.create()

        stadhuis_point = Point(STADHUIS['lon'], STADHUIS['lat'])
        arena_point = Point(ARENA['lon'], ARENA['lat'])
        filmhuis_eye_point = Point(FILMMUSEUM_EYE['lon'], FILMMUSEUM_EYE['lat'])
        blauwe_theehuis_point = Point(BLAUWE_THEEHUIS['lon'], BLAUWE_THEEHUIS['lat'])

        with freeze_time(now - timedelta(days=5)):
            signal = SignalFactory.create(reporter__email=self.reporter_1_email,
                                          status__state=workflow.BEHANDELING,
                                          location__geometrie=stadhuis_point,
                                          location__buurt_code=STADHUIS['buurt_code'],
                                          category_assignment__category=self.test_category)
            FeedbackFactory.create(_signal=signal, submitted_at=now, is_satisfied=False)

            # Child signals ("deelmeldingen") should not show up in the reporter context, as they are used internally.
            self.child_signals = SignalFactory.create_batch(size=2,
                                                            reporter__email=self.reporter_1_email,
                                                            parent=signal,
                                                            location__geometrie=stadhuis_point,
                                                            location__buurt_code=ARENA['buurt_code'],
                                                            category_assignment__category=self.test_category)

        with freeze_time(now - timedelta(days=4)):
            SignalFactory.create(reporter__email=self.reporter_1_email,
                                 status__state=workflow.BEHANDELING,
                                 location__geometrie=stadhuis_point,
                                 location__buurt_code=STADHUIS['buurt_code'],
                                 category_assignment__category=self.test_category)

        with freeze_time(now - timedelta(days=3)):
            signal = SignalFactory.create(reporter__email=self.reporter_1_email,
                                          status__state=workflow.AFGEHANDELD,
                                          location__geometrie=arena_point,
                                          location__area_code='arena',
                                          location__buurt_code=ARENA['buurt_code'],
                                          category_assignment__category=self.test_category)
            FeedbackFactory.create(_signal=signal, submitted_at=now, is_satisfied=False)

            SignalFactory.create(reporter__email=self.reporter_1_email,
                                 status__state=workflow.AFGEHANDELD,
                                 location__geometrie=filmhuis_eye_point,
                                 location__buurt_code=FILMMUSEUM_EYE['buurt_code'],
                                 category_assignment__category=self.test_category)

            signal = SignalFactory.create(reporter__email=self.reporter_1_email,
                                          status__state=workflow.AFGEHANDELD,
                                          location__geometrie=blauwe_theehuis_point,
                                          location__buurt_code=BLAUWE_THEEHUIS['buurt_code'],
                                          category_assignment__category=self.test_category)
            FeedbackFactory.create(_signal=signal, submitted_at=now, is_satisfied=True)

        self.reporter_1_signals = Signal.objects.filter(
            (Q(parent__isnull=True) & Q(children__isnull=True)) | Q(children__isnull=False),
            reporter__email=self.reporter_1_email
        )

        self.anonymous_signals = [
            SignalFactory.create(reporter__email=None,
                                 status__state=workflow.BEHANDELING,
                                 location__geometrie=filmhuis_eye_point,
                                 location__buurt_code=FILMMUSEUM_EYE['buurt_code'],
                                 category_assignment__category=self.test_category),
            SignalFactory.create(reporter__email='',
                                 status__state=workflow.BEHANDELING,
                                 location__geometrie=blauwe_theehuis_point,
                                 location__buurt_code=BLAUWE_THEEHUIS['buurt_code'],
                                 category_assignment__category=self.test_category)
        ]

        self.reporter_2_signals = SignalFactory.create_batch(size=5,
                                                             reporter__email=self.reporter_2_email,
                                                             location__geometrie=filmhuis_eye_point,
                                                             location__buurt_code=FILMMUSEUM_EYE['buurt_code'],
                                                             category_assignment__category=self.test_category)

    def test_get_signal_context(self):
        self.client.force_authenticate(user=self.superuser)

        signal_id = self.reporter_1_signals[0].pk
        response = self.client.get(f'/signals/v1/private/signals/{signal_id}/context/')
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertIsNotNone(response_data['near']['signal_count'])
        self.assertEqual(response_data['near']['signal_count'], 3)

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

    @skip('TODO Fix failing test')
    def test_get_signal_context_geography_detail(self):
        self.client.force_authenticate(user=self.superuser)

        signal_id = self.reporter_1_signals[2].pk
        response = self.client.get(f'/signals/v1/private/signals/{signal_id}/context/near/geography')
        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        self.assertEqual(len(response_json['features']), 2)

        signal_id = self.reporter_1_signals[3].pk
        response = self.client.get(f'/signals/v1/private/signals/{signal_id}/context/near/geography')
        self.assertEqual(response.status_code, 200)

        # TODO: Fix this test case
        # response_json = response.json()
        # self.assertEqual(len(response_json['features']), 0)

    def test_get_anonymous_signals_context(self):
        self.client.force_authenticate(user=self.superuser)

        for signal in self.anonymous_signals:
            response = self.client.get(f'/signals/v1/private/signals/{signal.pk}/context/')
            self.assertEqual(response.status_code, 200)

            response_data = response.json()
            self.assertIsNotNone(response_data['near'])

            self.assertEqual(response_data['reporter'], None)

    def test_get_anonymous_signals_context_reporter_detail(self):
        self.client.force_authenticate(user=self.superuser)

        for signal in self.anonymous_signals:
            response = self.client.get(f'/signals/v1/private/signals/{signal.pk}/context/reporter/')
            self.assertEqual(response.status_code, 404)

    def test_get_anonymous_signals_context_geography_detail(self):
        self.client.force_authenticate(user=self.superuser)

        for signal in self.anonymous_signals:
            response = self.client.get(f'/signals/v1/private/signals/{signal.pk}/context/near/geography/')
            self.assertEqual(response.status_code, 200)


class TestSignalContextPermissions(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    # Accessing SignalContext must follow the same access rules as the signals.
    # Specifically: rules around categories and departments must be followed.
    # ... but like with child signals brief information about Signals of the
    # same reporter must be available, even if those signals would not be
    # accessible.
    detail_endpoint = '/signals/v1/private/signals/{}'
    context_endpoint = '/signals/v1/private/signals/{}/context/'
    context_reporter_endpoint = '/signals/v1/private/signals/{}/context/reporter/'
    context_near_endpoint = '/signals/v1/private/signals/{}/context/near/geography/'

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

        url = self.context_near_endpoint.format(self.signal_no.id)
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

        url = self.context_near_endpoint.format(self.signal_yes.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
