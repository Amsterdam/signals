# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2022 Gemeente Amsterdam
from datetime import timedelta

from django.conf import settings
from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone
from freezegun import freeze_time

from signals.apps.feedback.factories import (
    FeedbackFactory,
    StandardAnswerFactory,
    StandardAnswerTopicFactory
)
from signals.apps.feedback.models import Feedback, StandardAnswer
from signals.apps.feedback.routers import feedback_router
from signals.apps.feedback.utils import get_feedback_urls
from signals.apps.signals import workflow
from signals.apps.signals.factories import SignalFactoryValidLocation
from signals.apps.signals.models import Signal
from signals.test.utils import SignalsBaseApiTestCase

# We want to keep these tests confined to the reusable application itself, see:
# https://docs.djangoproject.com/en/2.1/topics/testing/tools/#urlconf-configuration


class NameSpace:
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
            self.signal = SignalFactoryValidLocation(
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
        """Test that we receive an JSON object containing the signal_id (signal.uuid) HTTP 200 reply."""
        token = self.feedback.token

        with freeze_time(self.t_now):
            response = self.client.get('/forms/{}/'.format(token))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {'signal_id': f'{self.feedback._signal.uuid}'})

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
            self.assertIn(reason, self.feedback.text_list)

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

    def test_send_mail_is_satisfied_false_feedback_email(self):
        """"
        if is_satisfied is false is should send an email
        """
        self.assertEqual(len(mail.outbox), 0)
        token = self.feedback.token
        data = {
            'allows_contact': True,
            'text': 'probleem niet opgelost.',
            'is_satisfied': False,
        }

        with freeze_time(self.t_now):
            response = self.client.put(
                '/forms/{}/'.format(token),
                data=data,
                format='json',
            )
            self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)

    def test_send_mail_is_satisfied_true_feedback_email(self):
        """"
        if is_satisfied is true is should not send an email
        """
        self.assertEqual(len(mail.outbox), 0)
        token = self.feedback.token
        data = {
            'allows_contact': True,
            'text': 'opgelost.',
            'is_satisfied': True,
        }

        with freeze_time(self.t_now):
            response = self.client.put(
                '/forms/{}/'.format(token),
                data=data,
                format='json',
            )
            self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    def test_text_to_text_list(self):
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
        self.assertIsNone(self.feedback.text)
        self.assertIn(reason, self.feedback.text_list)

    def test_no_contact(self):
        """
        Test to not send an email when allow_contact is set false
        """
        token = self.feedback.token
        data = {
            'is_satisfied': False,
            'allows_contact': False,
            'text': 'reason',
            'text_area': 'explanation',
        }
        with freeze_time(self.t_now):
            response = self.client.put(
                '/forms/{}/'.format(token),
                data=data,
                format='json',
            )
            self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    def test_allows_contact(self):
        """
        Test to send an email when allow_contact is set True
        """
        token = self.feedback.token
        data = {
            'is_satisfied': False,
            'allows_contact': True,
            'text': 'reason',
            'text_area': 'explanation',
        }
        with freeze_time(self.t_now):
            response = self.client.put(
                '/forms/{}/'.format(token),
                data=data,
                format='json',
            )
            self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)

    @override_settings(FEATURE_FLAGS={
        "REPORTER_MAIL_CONTACT_FEEDBACK_ALLOWS_CONTACT_ENABLED": False
    })
    def test_allows_contact_feature_flag_false(self):
        """
        With the feature flag disabled still send emails even if allows contact is False
        """
        token = self.feedback.token
        data = {
            'is_satisfied': False,
            'allows_contact': False,
            'text': 'reason',
            'text_area': 'explanation',
        }
        with freeze_time(self.t_now):
            response = self.client.put(
                '/forms/{}/'.format(token),
                data=data,
                format='json',
            )
            self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)

    def test_text_and_text_list(self):
        """Test that the feedback can be PUT once."""
        token = self.feedback.token
        reason = 'testen is leuk'
        multi_reason = ['dit is een test', 'dit is een 2de test']
        explanation = 'ook voor de lunch'

        data = {
            'is_satisfied': True,
            'allows_contact': True,
            'text': reason,
            'text_list': multi_reason,
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
        self.assertIsNone(self.feedback.text)
        multi_reason.append(reason)
        self.assertEqual(multi_reason, self.feedback.text_list)

    def test_text_list(self):
        """Test that the feedback can be PUT once."""
        token = self.feedback.token
        multi_reason = ['dit is een test', 'dit is een 2de test']
        explanation = 'ook voor de lunch'

        data = {
            'is_satisfied': True,
            'allows_contact': True,
            'text_list': multi_reason,
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
        self.assertIsNone(self.feedback.text)
        self.assertEqual(multi_reason, self.feedback.text_list)


@override_settings(ROOT_URLCONF=test_urlconf)
class TestStandardAnswers(SignalsBaseApiTestCase):
    def setUp(self):
        StandardAnswer.objects.all().delete()
        self.topic_1 = StandardAnswerTopicFactory(name='topic_1', order=0)
        self.topic_2 = StandardAnswerTopicFactory(name='topic_2', order=1)
        self.standard_answer_1 = StandardAnswerFactory(
            is_visible=True, is_satisfied=True, topic=self.topic_1, order=2)
        self.standard_answer_2 = StandardAnswerFactory(
            is_visible=True, is_satisfied=False, topic=self.topic_1, order=0)
        self.standard_answer_3 = StandardAnswerFactory(
            is_visible=False, is_satisfied=True, topic=self.topic_2, order=0)
        self.standard_answer_4 = StandardAnswerFactory(
            is_visible=False, is_satisfied=False, topic=self.topic_2, order=5)
        self.standard_answer_5 = StandardAnswerFactory(
            is_visible=True, is_satisfied=False, topic=None)

    def test_setup(self):
        response = self.client.get('/standard_answers/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(StandardAnswer.objects.count(), 5)
        self.assertEqual(response.json()['count'], 3)

    def test_factories(self):
        self.assertEqual(StandardAnswer.objects.count(), 5)

        self.assertIn('POSITIEF ', str(self.standard_answer_1))
        self.assertIn('NEGATIEF ', str(self.standard_answer_2))
        self.assertIn('POSITIEF ', str(self.standard_answer_3))
        self.assertIn('NEGATIEF ', str(self.standard_answer_4))

    def test_ordering_topics(self):
        self.standard_answer_3.is_visible = True
        self.standard_answer_4.is_visible = True
        self.standard_answer_3.save()
        self.standard_answer_4.save()
        response = self.client.get('/standard_answers/')
        expected_order = [
            [self.standard_answer_2.text, self.topic_1.text],
            [self.standard_answer_1.text, self.topic_1.text],
            [self.standard_answer_3.text, self.topic_2.text],
            [self.standard_answer_4.text, self.topic_2.text],
            [self.standard_answer_5.text, None],

        ]
        response_order = [[item['text'], item['topic']] for item in response.json()['results']]
        self.assertEqual(expected_order, response_order)


class TestUtils(TestCase):
    def setUp(self):
        self.feedback = FeedbackFactory()

    def test_link_generation_with_environment_set_frontend_url_set(self):
        test_frontend_urls = ['https://acc.meldingen.amsterdam.nl', 'https://meldingen.amsterdam.nl',
                              'https://random.net', ]
        for test_frontend_url in test_frontend_urls:
            with override_settings(FRONTEND_URL=test_frontend_url):
                pos_url, neg_url = get_feedback_urls(self.feedback)

                self.assertIn(test_frontend_url, pos_url)
                self.assertIn(test_frontend_url, neg_url)

    def test_link_generation_no_environment_set(self):
        pos_url, neg_url = get_feedback_urls(self.feedback)
        self.assertEqual(f'{settings.FRONTEND_URL}/kto/ja/{self.feedback.token}', pos_url)
        self.assertEqual(f'{settings.FRONTEND_URL}/kto/nee/{self.feedback.token}', neg_url)
