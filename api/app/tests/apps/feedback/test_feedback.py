from datetime import timedelta
from unittest import mock

from django.core import mail
from django.test import override_settings
from django.urls import include, path
from django.utils import timezone
from freezegun import freeze_time
from rest_framework import routers

from signals.apps.feedback.views import FeedbackViewSet, StandardAnswerViewSet
from signals.apps.feedback.models import Feedback, StandardAnswer
from signals.apps.signals import workflow
from signals.apps.signals.models import Signal
from tests.test import SIAReadWriteUserMixin, SignalsBaseApiTestCase
from tests.apps.feedback.factories import FeedbackFactory, StandardAnswerFactory
from tests.apps.signals.factories import ReporterFactory, SignalFactoryValidLocation

# We want to keep these tests confined to the reusable application itself, see:
# https://docs.djangoproject.com/en/2.1/topics/testing/tools/#urlconf-configuration

class NameSpace():
    pass


test_router = routers.SimpleRouter()
test_router.register(r'standard_answers', StandardAnswerViewSet)
test_router.register(r'forms', FeedbackViewSet)

test_urlconf = NameSpace()
test_urlconf.urlpatterns = test_router.urls


@override_settings(ROOT_URLCONF=test_urlconf)
class TestFeedbackFlow(SignalsBaseApiTestCase):
    def setUp(self):
        # Times for various actions (assumes a 14 day window for feedback).
        self.t_now = '2019-04-01 12:00:00'
        self.t_creation = '2019-03-01 12:00:00'
        self.t_expired = '2019-03-02 12:00:00'
        self.t_received = '2019-03-29 12:00:00'

        # Setup our test signal and feedback instances
        with freeze_time(self.t_creation):
            self.reporter = ReporterFactory()
            self.signal = SignalFactoryValidLocation(
                reporter=self.reporter,
            )

        with freeze_time(self.t_now):
            self.feedback = FeedbackFactory(
                submitted_at=None,
                _signal=self.signal,
            )

        with freeze_time(self.t_expired):
            self.feedback_expired = FeedbackFactory(
                submitted_at=None,
                _signal=self.signal,
            )

        with freeze_time(self.t_received):
            self.feedback_received = FeedbackFactory(
                submitted_at=timezone.now() - timedelta(days=5),
                _signal=self.signal,
            )


    def test_setup(self):
        self.assertEqual(Feedback.objects.count(), 3)

    def test_404_if_no_feedback_requested(self):
        response = self.client.get('/forms/DIT_IS_GEEN_UUID/')
        self.assertEqual(response.status_code, 404)

    def test_410_gone_too_late(self):
        uuid = self.feedback_expired.uuid

        with freeze_time(self.t_now):
            response = self.client.get('/forms/{}/'.format(uuid))
            self.assertEqual(response.status_code, 410)  # faalt!
            self.assertEqual(response.json()['detail'], 'too late')

            response = self.client.put('/forms/{}/'.format(uuid), data={})
            self.assertEqual(response.status_code, 410)
            self.assertEqual(response.json()['detail'], 'too late')

    def test_410_gone_filled_out(self):
        """Test that we receive correct HTTP 410 reply when form filled out already"""
        uuid = self.feedback_received.uuid

        with freeze_time(self.t_now):
            response = self.client.get('/forms/{}/'.format(uuid))
            self.assertEqual(response.status_code, 410)
            self.assertEqual(response.json()['detail'], 'filled out')

            response = self.client.put('/forms/{}/'.format(uuid), data={})
            self.assertEqual(response.status_code, 410)
            self.assertEqual(response.json()['detail'], 'filled out')

    def test_200_if_feedback_requested(self):
        """Test that we receive an empty JSON object HTTP 200 reply."""
        uuid = self.feedback.uuid

        with freeze_time(self.t_now):
            response = self.client.get('/forms/{}/'.format(uuid))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {})

    def test_200_on_submit_feedback(self):
        """Test that the feedback can be PUT once."""
        uuid = self.feedback.uuid
        reason = 'testen is leuk'

        data = {
            'is_satisfied': True,
            'allows_contact': True,
            'text': reason,
        }

        with freeze_time(self.t_now):
            response = self.client.put(
                '/forms/{}/'.format(uuid),
                data=data
            )
            self.assertEqual(response.status_code, 200)

            self.feedback.refresh_from_db()
            self.assertEqual(self.feedback.is_satisfied, True)
            self.assertEqual(self.feedback.allows_contact, True)
            self.assertEqual(self.feedback.text, reason)


@override_settings(ROOT_URLCONF=test_urlconf)
class TestStandardAnswers(SignalsBaseApiTestCase):
    def setUp(self):
        StandardAnswerFactory(is_visible=True, is_satisfied=True)
        StandardAnswerFactory(is_visible=True, is_satisfied=False)
        StandardAnswerFactory(is_visible=False, is_satisfied=True)
        StandardAnswerFactory(is_visible=False, is_satisfied=False)

    def test_setup(self):
        response = self.client.get('/standard_answers/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(StandardAnswer.objects.count(), 4)
        self.assertEqual(response.json()['count'], 2)

    def test_factories(self):
        self.assertEqual(StandardAnswer.objects.count(), 4)
