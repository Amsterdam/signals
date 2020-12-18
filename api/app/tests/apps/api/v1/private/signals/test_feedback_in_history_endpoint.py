import os

from django.contrib.auth.models import Permission

from signals.apps.feedback.factories import FeedbackFactory
from signals.apps.signals.factories import SignalFactory
from tests.test import SIAReadWriteUserMixin, SignalsBaseApiTestCase

THIS_DIR = os.path.dirname(__file__)
JSON_SCHEMA_DIR = os.path.join(THIS_DIR, '..', 'json_schema')


class TestHistoryForFeedback(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    endpoint = '/signals/v1/private/signals/'

    history_json_schema_path = os.path.join(JSON_SCHEMA_DIR, 'get_signals_v1_private_signals_{pk}_history.json')
    signal_history_schema = None

    def setUp(self):
        # Load the JSON Schema's
        self.signal_history_schema = self.load_json_schema(self.history_json_schema_path)

        # Make sure that we have a user who can read from all Categories
        self.sia_read_write_user.user_permissions.add(Permission.objects.get(codename='sia_can_view_all_categories'))

    def test_submit_feedback_check_history(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        signal = SignalFactory.create()

        # check history before submitting feedback
        response = self.client.get(f'/signals/v1/private/signals/{signal.pk}/history')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 6)

        # Note the unhappy flow regarding feedback is tested in the feedback
        # app. Here we only check that it shows up in the history.
        feedback = FeedbackFactory(_signal=signal, is_satisfied=None)
        post_data = {
            'is_satisfied': True,
            'allows_contact': False,
            'text': 'De zon schijnt.',
            'text_extra': 'maar niet heus',
        }

        response = self.client.put(f'/signals/v1/public/feedback/forms/{feedback.token}', data=post_data, format='json')
        self.assertEqual(response.status_code, 200)

        # check that feedback object in db is updated
        feedback.refresh_from_db()
        self.assertEqual(feedback.is_satisfied, True)
        self.assertNotEqual(feedback.submitted_at, None)

        # check have an entry in the history for the feedback
        response = self.client.get(f'/signals/v1/private/signals/{signal.pk}/history')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 7)

        # check that filtering by RECEIVE_FEEDBACK works
        response = self.client.get(f'/signals/v1/private/signals/{signal.pk}/history',
                                   data={'what': 'RECEIVE_FEEDBACK'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_history_entry_description_property(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        signal = SignalFactory.create()

        feedback = FeedbackFactory(_signal=signal, is_satisfied=None)
        post_data = {
            'is_satisfied': True,
            'allows_contact': False,
            'text': 'De zon schijnt.',
            'text_extra': 'maar niet heus',
        }
        response = self.client.put(f'/signals/v1/public/feedback/forms/{feedback.token}', data=post_data, format='json')
        self.assertEqual(response.status_code, 200)

        # check the rendering
        response = self.client.get(f'/signals/v1/private/signals/{signal.pk}/history',
                                   data={'what': 'RECEIVE_FEEDBACK'})
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertEqual(len(response_data), 1)
        history_entry = response_data[0]

        self.assertIn('Ja, de melder is tevreden', history_entry['description'])
        self.assertIn('Waarom: De zon schijnt.', history_entry['description'])
        self.assertIn('Toelichting: maar niet heus', history_entry['description'])
        self.assertIn('Toestemming contact opnemen: Nee', history_entry['description'])
