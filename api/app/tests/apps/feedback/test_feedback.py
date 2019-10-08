import copy
from datetime import timedelta
from unittest import mock

from django.conf import settings
from django.test import TestCase, override_settings
from django.utils import timezone
from freezegun import freeze_time

from signals.apps.feedback import app_settings as feedback_settings
from signals.apps.feedback.models import Feedback, StandardAnswer
from signals.apps.feedback.routers import feedback_router
from signals.apps.feedback.utils import get_feedback_urls
from signals.apps.signals import workflow
from signals.apps.signals.models import Signal
from tests.apps.feedback.factories import FeedbackFactory, StandardAnswerFactory
from tests.apps.signals.factories import ReporterFactory, SignalFactoryValidLocation
from tests.test import SignalsBaseApiTestCase

# We want to keep these tests confined to the reusable application itself, see:
# https://docs.djangoproject.com/en/2.1/topics/testing/tools/#urlconf-configuration


class NameSpace():
    pass


test_urlconf = NameSpace()
test_urlconf.urlpatterns = feedback_router.urls


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
                status__state=workflow.AFGEHANDELD,
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

        # Setup a standard answer that triggers a request to reopen.
        self.sa_reopens = StandardAnswerFactory.create(
            text='Ik ben niet blij met de afhandeling, duurde te lang.',
            is_satisfied=False,
            reopens_when_unhappy=True,
        )

        self.sa_no_sideeffect = StandardAnswerFactory.create(
            text='Ik ben niet blij. Blah, blah.',
            is_satisfied=False,
            reopens_when_unhappy=False,
        )

    def test_setup(self):
        self.assertEqual(Feedback.objects.count(), 3)

    def test_404_if_no_feedback_requested(self):
        response = self.client.get('/forms/DIT_IS_GEEN_token/')
        self.assertEqual(response.status_code, 404)

    def test_410_gone_too_late(self):
        token = self.feedback_expired.token

        with freeze_time(self.t_now):
            response = self.client.get('/forms/{}/'.format(token))
            self.assertEqual(response.status_code, 410)  # faalt!
            self.assertEqual(response.json()['detail'], 'too late')

            response = self.client.put('/forms/{}/'.format(token), data={})
            self.assertEqual(response.status_code, 410)
            self.assertEqual(response.json()['detail'], 'too late')

    def test_410_gone_filled_out(self):
        """Test that we receive correct HTTP 410 reply when form filled out already"""
        token = self.feedback_received.token

        with freeze_time(self.t_now):
            response = self.client.get('/forms/{}/'.format(token))
            self.assertEqual(response.status_code, 410)
            self.assertEqual(response.json()['detail'], 'filled out')

            response = self.client.put('/forms/{}/'.format(token), data={})
            self.assertEqual(response.status_code, 410)
            self.assertEqual(response.json()['detail'], 'filled out')

    def test_200_if_feedback_requested(self):
        """Test that we receive an empty JSON object HTTP 200 reply."""
        token = self.feedback.token

        with freeze_time(self.t_now):
            response = self.client.get('/forms/{}/'.format(token))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {})

    def test_200_on_submit_feedback(self):
        """Test that the feedback can be PUT once."""
        token = self.feedback.token
        reason = 'testen is leuk'
        explanation = 'ook voor de lunch'

        data = {
            'is_satisfied': True,
            'allows_contact': True,
            'text': reason,
            'text_area': explanation,
        }

        with freeze_time(self.t_now):
            response = self.client.put(
                '/forms/{}/'.format(token),
                data=data,
                format='json',
            )
            self.assertEqual(response.status_code, 200)

            self.feedback.refresh_from_db()
            self.assertEqual(self.feedback.is_satisfied, True)
            self.assertEqual(self.feedback.allows_contact, True)
            self.assertEqual(self.feedback.text, reason)

    def test_400_on_submit_feedback_without_is_satisfied(self):
        """Test that the feedback can be PUT once."""
        token = self.feedback.token
        reason = 'testen is leuk'
        explanation = 'ook voor de lunch'

        data = {
            'allows_contact': True,
            'text': reason,
            'text_area': explanation,
        }

        with freeze_time(self.t_now):
            response = self.client.put(
                '/forms/{}/'.format(token),
                data=data,
                format='json',
            )
            self.assertEqual(response.status_code, 400)

    def test_reopen_requested_on_unsatisfied_standard_answer(self):
        """Certain standard answers (in feedback) lead to "reopen requested" state."""
        token = self.feedback.token
        data = {
            'allows_contact': False,
            'text': self.sa_reopens.text,
            'is_satisfied': False,
        }

        with freeze_time(self.t_now):
            response = self.client.put(
                '/forms/{}/'.format(token),
                data=data,
                format='json',
            )
            self.assertEqual(response.status_code, 200)

        self.signal.refresh_from_db()
        self.assertEqual(self.signal.status.state, workflow.VERZOEK_TOT_HEROPENEN)

    def test_reopen_requested_on_unsatisfied_custom_answer(self):
        """All custom unsatisfied answers (in feedback) lead to "reopen requested" state."""
        token = self.feedback.token
        data = {
            'allows_contact': False,
            'text': 'MEH, probleem niet opgelost.',
            'is_satisfied': False,
        }

        with freeze_time(self.t_now):
            response = self.client.put(
                '/forms/{}/'.format(token),
                data=data,
                format='json',
            )
            self.assertEqual(response.status_code, 200)

        self.signal.refresh_from_db()
        self.assertEqual(self.signal.status.state, workflow.VERZOEK_TOT_HEROPENEN)

    def test_no_reopen_requested_on_unsatisfied_and_known_feedback(self):
        """Some negative feedback is explicitly marked not to trigger reopen requested."""
        token = self.feedback.token
        data = {
            'allows_contact': False,
            'text': self.sa_no_sideeffect.text,
            'is_satisfied': False,
        }

        with freeze_time(self.t_now):
            response = self.client.put(
                '/forms/{}/'.format(token),
                data=data,
                format='json',
            )
            self.assertEqual(response.status_code, 200)

        self.signal.refresh_from_db()
        self.assertEqual(self.signal.status.state, workflow.AFGEHANDELD)

    def test_no_reopen_requested_when_not_in_state_afgehandeld(self):
        """Only request reopen from AFGEHANDELD state."""
        with freeze_time(self.t_now):
            # Reopen the test signal (so it is no longer in AFGEHANDELD).
            payload = {
                'text': 'De melder is niet tevreden blijkt uit feedback. Zo nodig heropenen.',
                'state': workflow.HEROPEND,
            }
            Signal.actions.update_status(payload, self.signal)

            # Send feedback that potentially reopens a signal (should not happen in this test).
            token = self.feedback.token
            data = {
                'allows_contact': False,
                'text': self.sa_reopens.text,
                'is_satisfied': False,
            }

            response = self.client.put(
                '/forms/{}/'.format(token),
                data=data,
                format='json',
            )
            self.assertEqual(response.status_code, 200)

        # Assert that nothing happened.
        self.signal.refresh_from_db()
        self.assertEqual(self.signal.status.state, workflow.HEROPEND)

    def test_no_reopen_requested_on_positive_feedback(self):
        """Positive feedback should never request a reopen"""
        # Create a positive feedback StandardAnswer that could possibly lead to
        # the status reopen requested.
        sa_positive = StandardAnswerFactory.create(
            text='Ik ben blij met de afhandeling.',
            is_satisfied=True,
            reopens_when_unhappy=True,
        )
        status_id_before = self.signal.status.id

        with freeze_time(self.t_now):
            # Send feedback that potentially reopens a signal (should not happen in this test).
            token = self.feedback.token
            data = {
                'allows_contact': False,
                'text': sa_positive.text,
                'is_satisfied': True,  # should not be able to override, refactor into separate test
            }

            response = self.client.put(
                '/forms/{}/'.format(token),
                data=data,
                format='json',
            )
            self.assertEqual(response.status_code, 200)

        # Assert that nothing happened.
        self.signal.refresh_from_db()
        self.assertEqual(self.signal.status.state, workflow.AFGEHANDELD)
        self.assertEqual(status_id_before, self.signal.status.id)


@override_settings(ROOT_URLCONF=test_urlconf)
class TestStandardAnswers(SignalsBaseApiTestCase):
    def setUp(self):
        StandardAnswer.objects.all().delete()
        self.standard_answer_1 = StandardAnswerFactory(is_visible=True, is_satisfied=True)
        self.standard_answer_2 = StandardAnswerFactory(is_visible=True, is_satisfied=False)
        self.standard_answer_3 = StandardAnswerFactory(is_visible=False, is_satisfied=True)
        self.standard_answer_4 = StandardAnswerFactory(is_visible=False, is_satisfied=False)

    def test_setup(self):
        response = self.client.get('/standard_answers/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(StandardAnswer.objects.count(), 4)
        self.assertEqual(response.json()['count'], 2)

    def test_factories(self):
        self.assertEqual(StandardAnswer.objects.count(), 4)

        self.assertIn('POSITIEF ', str(self.standard_answer_1))
        self.assertIn('NEGATIEF ', str(self.standard_answer_2))
        self.assertIn('POSITIEF ', str(self.standard_answer_3))
        self.assertIn('NEGATIEF ', str(self.standard_answer_4))


class TestUtils(TestCase):
    def setUp(self):
        self.feedback = FeedbackFactory()

    def test_link_generation_with_environment_set(self):
        env_fe_mapping = copy.deepcopy(getattr(
            settings,
            'FEEDBACK_ENV_FE_MAPPING',
            feedback_settings.FEEDBACK_ENV_FE_MAPPING,
        ))

        for environment, fe_location in env_fe_mapping.items():
            env = {'ENVIRONMENT': environment}
            with mock.patch.dict('os.environ', env, clear=True):
                pos_url, neg_url = get_feedback_urls(self.feedback)

                print(environment, fe_location, pos_url)
                print(environment, fe_location, neg_url, '\n')
                self.assertIn(fe_location, pos_url)
                self.assertIn(fe_location, neg_url)

    def test_link_generation_no_environment_set(self):
        with mock.patch.dict('os.environ', {}, clear=True):
            pos_url, neg_url = get_feedback_urls(self.feedback)
            self.assertEqual('http://dummy_link/kto/yes/123', pos_url)
            self.assertEqual('http://dummy_link/kto/no/123', neg_url)
