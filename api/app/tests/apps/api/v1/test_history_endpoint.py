import os
from datetime import timedelta

from django.utils import timezone
from freezegun import freeze_time

from signals.apps.feedback.factories import FeedbackFactory
from signals.apps.feedback.models import Feedback
from signals.apps.signals import workflow
from signals.apps.signals.factories import SignalFactory, SignalFactoryValidLocation
from signals.apps.signals.models import Category, History, Signal
from tests.test import SIAReadUserMixin, SIAReadWriteUserMixin, SignalsBaseApiTestCase

THIS_DIR = os.path.dirname(__file__)
SIGNALS_TEST_DIR = os.path.join(os.path.split(THIS_DIR)[0], '..', 'signals')


class TestHistoryAction(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    def setUp(self):
        self.signal = SignalFactory.create()

        self.list_history_schema = self.load_json_schema(
            os.path.join(
                THIS_DIR,
                'json_schema',
                'get_signals_v1_private_signals_{pk}_history.json'
            )
        )

    def test_history_action_present(self):
        response = self.client.get(f'/signals/v1/private/signals/{self.signal.id}/history')
        self.assertEqual(response.status_code, 401)

        self.client.force_authenticate(user=self.sia_read_write_user)
        response = self.client.get(f'/signals/v1/private/signals/{self.signal.id}/history')
        self.assertEqual(response.status_code, 200)

        # JSONSchema validation
        data = response.json()
        self.assertJsonSchema(self.list_history_schema, data)

    def test_history_endpoint_rendering(self):
        history_entries = History.objects.filter(_signal__id=self.signal.pk)

        self.client.force_authenticate(user=self.sia_read_write_user)
        response = self.client.get(f'/signals/v1/private/signals/{self.signal.id}/history')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data), history_entries.count())

        # JSONSchema validation
        self.assertJsonSchema(self.list_history_schema, data)

    def test_history_entry_contents(self):
        keys = ['identifier', 'when', 'what', 'action', 'description', 'who', '_signal']

        self.client.force_authenticate(user=self.sia_read_write_user)
        response = self.client.get(f'/signals/v1/private/signals/{self.signal.id}/history')
        self.assertEqual(response.status_code, 200)

        # JSONSchema validation
        data = response.json()
        self.assertJsonSchema(self.list_history_schema, data)

        for entry in data:
            for k in keys:
                self.assertIn(k, entry)

    def test_update_shows_up(self):
        # Get a baseline for the Signal history
        self.client.force_authenticate(user=self.sia_read_write_user)
        response = self.client.get(f'/signals/v1/private/signals/{self.signal.id}/history')
        n_entries = len(response.json())
        self.assertEqual(response.status_code, 200)

        # Update the Signal status, and ...
        status = Signal.actions.update_status(
            {
                'text': 'DIT IS EEN TEST',
                'state': workflow.BEHANDELING,
                'user': self.user,
            },
            self.signal
        )

        # ... check that the new status shows up as most recent entry in history.
        response = self.client.get(f'/signals/v1/private/signals/{self.signal.id}/history')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), n_entries + 1)

        # JSONSchema validation
        data = response.json()
        self.assertJsonSchema(self.list_history_schema, data)

        new_entry = data[0]  # most recent status should be first
        self.assertEqual(new_entry['who'], self.user.username)
        self.assertEqual(new_entry['description'], status.text)

    def test_sla_in_history(self):
        # Get a baseline for the Signal history
        self.client.force_authenticate(user=self.sia_read_write_user)
        response = self.client.get(f'/signals/v1/private/signals/{self.signal.id}/history')
        self.assertEqual(response.status_code, 200)

        # JSONSchema validation
        data = response.json()
        self.assertJsonSchema(self.list_history_schema, data)

        what_in_history = [entry['what'] for entry in data]
        self.assertIn('UPDATE_CATEGORY_ASSIGNMENT', what_in_history)
        self.assertEquals(1, what_in_history.count('UPDATE_CATEGORY_ASSIGNMENT'))

        self.assertIn('UPDATE_SLA', what_in_history)
        self.assertEquals(1, what_in_history.count('UPDATE_SLA'))

        actions_in_history = [entry['action'] for entry in data]
        self.assertIn('Servicebelofte:', actions_in_history)

        sla_description_in_history = [entry['description'] for entry in data if entry['action'] == 'Servicebelofte:']  # noqa
        self.assertEqual(self.signal.category_assignments.all().order_by('created_at')[0].category.handling_message,
                         sla_description_in_history[0])

    def test_sla_only_once_in_history(self):
        # Update the Signal category, and check that we only have the original SLA hadnling message in the history
        now = timezone.now()
        hours = 1
        categories = Category.objects.filter(parent__isnull=False).order_by('?')[:5]
        for category in categories:
            with freeze_time(now + timedelta(hours=hours)):
                Signal.actions.update_category_assignment(
                    {
                        'category': category,
                        'text': 'DIT IS EEN TEST',
                    },
                    self.signal
                )
                hours += 1

        # Get a baseline for the Signal history
        self.client.force_authenticate(user=self.sia_read_write_user)
        response = self.client.get(f'/signals/v1/private/signals/{self.signal.id}/history')
        self.assertEqual(response.status_code, 200)

        # JSONSchema validation
        data = response.json()
        self.assertJsonSchema(self.list_history_schema, data)

        what_in_history = [entry['what'] for entry in data]
        self.assertIn('UPDATE_CATEGORY_ASSIGNMENT', what_in_history)
        self.assertEquals(6, what_in_history.count('UPDATE_CATEGORY_ASSIGNMENT'))

        self.assertIn('UPDATE_SLA', what_in_history)
        self.assertEquals(1, what_in_history.count('UPDATE_SLA'))

        sla_description_in_history = [entry['description'] for entry in data if entry['action'] == 'Servicebelofte:']  # noqa
        self.assertEqual(self.signal.category_assignments.all().order_by('created_at')[0].category.handling_message,
                         sla_description_in_history[0])


class TestHistoryForFeedback(SignalsBaseApiTestCase, SIAReadUserMixin):
    def setUp(self):
        self.signal = SignalFactoryValidLocation()
        self.feedback = FeedbackFactory(
            _signal=self.signal,
            is_satisfied=None,
        )

        self.feedback_endpoint = '/signals/v1/public/feedback/forms/{token}'
        self.history_endpoint = '/signals/v1/private/signals/{id}/history'

    def test_setup(self):
        self.assertEqual(Signal.objects.count(), 1)
        self.assertEqual(Feedback.objects.count(), 1)

        self.assertEqual(Feedback.objects.count(), 1)
        self.assertEqual(self.feedback.is_satisfied, None)
        self.assertEqual(self.feedback.submitted_at, None)

    def test_submit_feedback_check_history(self):
        # get a user privileged to read from API
        read_user = self.sia_read_user
        self.client.force_authenticate(user=read_user)
        history_url = self.history_endpoint.format(id=self.signal.id)

        # check history before submitting feedback
        response = self.client.get(history_url)
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertEqual(len(response_data), 6)

        # Note the unhappy flow regarding feedback is tested in the feedback
        # app. Here we only check that it shows up in the history.
        url = self.feedback_endpoint.format(token=self.feedback.token)
        payload = {
            'is_satisfied': True,
            'allows_contact': False,
            'text': 'De zon schijnt.',
            'text_extra': 'maar niet heus',
        }

        response = self.client.put(url, data=payload, format='json')
        self.assertEqual(response.status_code, 200)

        # check that feedback object in db is updated
        self.feedback.refresh_from_db()
        self.assertEqual(self.feedback.is_satisfied, True)
        self.assertNotEqual(self.feedback.submitted_at, None)

        # check have an entry in the history for the feedback
        response = self.client.get(history_url)
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertEqual(len(response_data), 7)

        # check that filtering by RECEIVE_FEEDBACK works
        response = self.client.get(history_url + '?what=RECEIVE_FEEDBACK')
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertEqual(len(response_data), 1)

    def test_history_entry_description_property(self):
        # equivalent to submitting feedback:
        text = 'TEXT'
        text_extra = 'TEXT_EXTRA'

        self.feedback.is_satisfied = True
        self.feedback.allows_contact = False
        self.feedback.text = text
        self.feedback.text_extra = text_extra
        self.feedback.submitted_at = self.feedback.created_at + timedelta(days=1)
        self.feedback.save()

        # check the rendering
        read_user = self.sia_read_user
        self.client.force_authenticate(user=read_user)
        history_url = self.history_endpoint.format(id=self.signal.id)

        response = self.client.get(history_url + '?what=RECEIVE_FEEDBACK')
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertEqual(len(response_data), 1)
        history_entry = response_data[0]

        self.assertIn('Ja, de melder is tevreden', history_entry['description'])
        self.assertIn(f'Waarom: {text}', history_entry['description'])
        self.assertIn(f'Toelichting: {text_extra}', history_entry['description'])
        self.assertIn('Toestemming contact opnemen: Nee', history_entry['description'])
