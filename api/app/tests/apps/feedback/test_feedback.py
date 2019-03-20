from datetime import timedelta

from django.test import override_settings
from django.urls import include, path
from django.utils import timezone
from freezegun import freeze_time
from rest_framework import routers

from signals.apps.feedback.views import FeedbackViewSet, StandardAnswerViewSet
from signals.apps.feedback.models import Feedback, StandardAnswer
from tests.test import SIAReadWriteUserMixin, SignalsBaseApiTestCase
from tests.apps.feedback.factories import FeedbackFactory, StandardAnswerFactory

# We want to keep these tests confined to the reusable application itself, see:
# https://docs.djangoproject.com/en/2.1/topics/testing/tools/#urlconf-configuration

class NameSpace():
    pass


test_router = routers.SimpleRouter()
test_router.register(r'standard_answers', StandardAnswerViewSet)
test_router.register(r'forms', FeedbackViewSet)

test_urlconf = NameSpace()
test_urlconf.urlpatterns = test_router.urls


@freeze_time('2019-03-20 12:00:00', tz_offset=0)
@override_settings(ROOT_URLCONF=test_urlconf)
class TestFeedbackFlow(SignalsBaseApiTestCase):
    def setUp(self):
        self.feedback = FeedbackFactory(
            is_satisfied=None,
            _signal__created_at=timezone.now(),
            requested_before=timezone.now() + timedelta(days=14),
        )
        self.feedback_expired = FeedbackFactory(
            _signal__created_at=timezone.now() - timedelta(days=28),
            requested_before=timezone.now() - timedelta(days=14),
        )
        self.feedback_received = FeedbackFactory(
            is_satisfied=True,
            _signal__created_at=timezone.now(),
            requested_before=timezone.now() + timedelta(days=14),
        )

    def test_setup(self):
        self.assertEqual(Feedback.objects.count(), 3)

    def test_404_if_no_feedback_requested(self):
        response = self.client.get('/forms/DIT_IS_GEEN_UUID/')
        self.assertEqual(response.status_code, 404)

    def test_410_gone_too_late(self):
        uuid = self.feedback_expired.uuid

        response = self.client.get('/forms/{}/'.format(uuid))
        self.assertEqual(response.status_code, 410)
        self.assertEqual(response.json()['detail'], 'too late')

        response = self.client.put('/forms/{}/'.format(uuid), data={})
        self.assertEqual(response.status_code, 410)
        self.assertEqual(response.json()['detail'], 'too late')

    def test_410_gone_filled_out(self):
        """Test that we receive correct HTTP 410 reply when form filled out already"""
        uuid = self.feedback_received.uuid

        response = self.client.get('/forms/{}/'.format(uuid))
        self.assertEqual(response.status_code, 410)
        self.assertEqual(response.json()['detail'], 'filled out')

        response = self.client.put('/forms/{}/'.format(uuid), data={})
        self.assertEqual(response.status_code, 410)
        self.assertEqual(response.json()['detail'], 'filled out')

    def test_200_if_feedback_requested(self):
        """Test that we receive an empty JSON object HTTP 200 reply."""
        uuid = self.feedback.uuid

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
