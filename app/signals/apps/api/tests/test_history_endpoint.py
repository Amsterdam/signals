# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2022 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
import os
from datetime import timedelta

from django.contrib.auth.models import Permission
from django.utils import timezone
from freezegun import freeze_time

from signals.apps.feedback.factories import FeedbackFactory
from signals.apps.feedback.models import Feedback
from signals.apps.signals import workflow
from signals.apps.signals.factories import (
    CategoryFactory,
    SignalFactory,
    SignalFactoryValidLocation
)
from signals.apps.signals.models import Category, History, Signal
from signals.apps.signals.models.category_assignment import CategoryAssignment
from signals.apps.signals.models.history import EMPTY_HANDLING_MESSAGE_PLACEHOLDER_MESSAGE
from signals.test.utils import SIAReadUserMixin, SIAReadWriteUserMixin, SignalsBaseApiTestCase

THIS_DIR = os.path.dirname(__file__)
SIGNALS_TEST_DIR = os.path.join(os.path.split(THIS_DIR)[0], '..', 'signals')


class TestHistoryAction(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    def setUp(self):
        self.signal = SignalFactory.create(user_assignment=None)

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

        self.sia_read_write_user.user_permissions.add(Permission.objects.get(codename='sia_can_view_all_categories'))
        self.client.force_authenticate(user=self.sia_read_write_user)
        response = self.client.get(f'/signals/v1/private/signals/{self.signal.id}/history')
        self.assertEqual(response.status_code, 200)

        # JSONSchema validation
        data = response.json()
        self.assertJsonSchema(self.list_history_schema, data)

    def test_history_endpoint_rendering(self):
        history_entries = History.objects.filter(_signal__id=self.signal.pk)

        self.sia_read_write_user.user_permissions.add(Permission.objects.get(codename='sia_can_view_all_categories'))
        self.client.force_authenticate(user=self.sia_read_write_user)
        response = self.client.get(f'/signals/v1/private/signals/{self.signal.id}/history')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data), history_entries.count())

        # JSONSchema validation
        self.assertJsonSchema(self.list_history_schema, data)

    def test_history_entry_contents(self):
        keys = ['identifier', 'when', 'what', 'action', 'description', 'who', '_signal']

        self.sia_read_write_user.user_permissions.add(Permission.objects.get(codename='sia_can_view_all_categories'))
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
        self.sia_read_write_user.user_permissions.add(Permission.objects.get(codename='sia_can_view_all_categories'))
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
        self.sia_read_write_user.user_permissions.add(Permission.objects.get(codename='sia_can_view_all_categories'))
        self.client.force_authenticate(user=self.sia_read_write_user)
        response = self.client.get(f'/signals/v1/private/signals/{self.signal.id}/history')
        self.assertEqual(response.status_code, 200)

        # JSONSchema validation
        data = response.json()
        self.assertJsonSchema(self.list_history_schema, data)

        what_in_history = [entry['what'] for entry in data]
        self.assertIn('UPDATE_CATEGORY_ASSIGNMENT', what_in_history)
        self.assertEqual(1, what_in_history.count('UPDATE_CATEGORY_ASSIGNMENT'))

        self.assertIn('UPDATE_SLA', what_in_history)
        self.assertEqual(1, what_in_history.count('UPDATE_SLA'))

        actions_in_history = [entry['action'] for entry in data]
        self.assertIn('Servicebelofte:', actions_in_history)

        sla_description_in_history = [entry['description'] for entry in data if entry['action'] == 'Servicebelofte:']  # noqa
        self.assertEqual(self.signal.category_assignments.all().order_by('created_at')[0].category.handling_message,
                         sla_description_in_history[0])

    def test_sla_only_once_in_history(self):
        # Update the Signal category, and check that we only have the original SLA handling message in the history
        now = timezone.now()
        hours = 1

        # Select 4 random subcategories that are not assigned to the signal yet
        categories = Category.objects.filter(
            parent__isnull=False,  # Must be a subcategory
            is_active=True,  # The category must be active
        ).exclude(
            id__in=self.signal.category_assignments.values_list('category_id', flat=True)  # noqa Exclude all previously assinged categories
        ).order_by(
            '?'  # Order random
        )[:5]  # Only 5 categories needed for this test
        self.assertEqual(5, categories.count())

        # Let's assign categories to the signal with an interval of 1 hour
        for category in categories:
            with freeze_time(now + timedelta(hours=hours)):
                Signal.actions.update_category_assignment(
                    {'category': category, 'text': 'DIT IS EEN TEST'}, self.signal
                )
                hours += 1
        self.signal.refresh_from_db()

        # Get a baseline for the Signal history
        self.sia_read_write_user.user_permissions.add(Permission.objects.get(codename='sia_can_view_all_categories'))
        self.client.force_authenticate(user=self.sia_read_write_user)
        response = self.client.get(f'/signals/v1/private/signals/{self.signal.id}/history')
        self.assertEqual(response.status_code, 200)

        # JSONSchema validation
        data = response.json()
        self.assertJsonSchema(self.list_history_schema, data)

        # Search for the category assignments in the history
        what_in_history = [entry['what'] for entry in data]
        self.assertIn('UPDATE_CATEGORY_ASSIGNMENT', what_in_history)
        self.assertEqual(categories.count() + 1, what_in_history.count('UPDATE_CATEGORY_ASSIGNMENT'))

        # The UPDATE_SLA can only be in the history once
        self.assertIn('UPDATE_SLA', what_in_history)
        self.assertEqual(1, what_in_history.count('UPDATE_SLA'))

        # The description in the history for UPDATE_SLA should match the handling message of the first assigned category
        sla_description_in_history = [entry['description'] for entry in data if entry['action'] == 'Servicebelofte:']
        self.assertEqual(self.signal.category_assignments.all().order_by('created_at')[0].category.handling_message,
                         sla_description_in_history[0])

    def test_handling_message_in_history_is_constant(self):
        # SIG-3555 because history is not tracked for the Category model and its
        # handling_message. Changing the handling_message will also change the
        # history of every Signal that has that Category associated with.
        # This test demonstrates the problem.
        message_1 = 'MESSAGE 1'
        message_2 = 'MESSAGE 2'

        cat1 = CategoryFactory.create(name='cat1', handling_message=message_1)
        cat2 = CategoryFactory.create(name='cat2')
        signal = SignalFactoryValidLocation(category_assignment__category=cat1)

        self.sia_read_write_user.user_permissions.add(Permission.objects.get(codename='sia_can_view_all_categories'))
        self.client.force_authenticate(user=self.sia_read_write_user)

        # Retrieve signal history before changing the Category handling message.
        response = self.client.get(f'/signals/v1/private/signals/{signal.id}/history' + '?what=UPDATE_SLA')
        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        self.assertEqual(len(response_json), 1)
        self.assertEqual(response_json[0]['description'], message_1)

        # Change handling message on category
        cat1.handling_message = message_2
        cat1.save()
        cat1.refresh_from_db()

        # Assign different category and then the same again, check handling messages.
        Signal.actions.update_category_assignment({'category': cat2}, signal)
        signal.refresh_from_db()
        Signal.actions.update_category_assignment({'category': cat1}, signal)
        response = self.client.get(f'/signals/v1/private/signals/{signal.id}/history' + '?what=UPDATE_SLA')
        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        self.assertEqual(len(response_json), 1)
        self.assertEqual(response_json[0]['description'], message_1)

        # check that the correct handling messages are stored:
        category_assignments = list(CategoryAssignment.objects.filter(_signal_id=signal.id).order_by('id'))
        self.assertEqual(category_assignments[0].stored_handling_message, message_1)
        self.assertEqual(category_assignments[2].stored_handling_message, message_2)

    def test_null_stored_handling_message(self):
        # SIG-3555 old complaints/Signals will have no stored handling messages on their associated CategoryAssignments.
        # This test fakes that by setting one category's handling message to null and checks that the correct
        # placeholder is returned.
        message_1 = None

        cat1 = CategoryFactory.create(name='cat1', handling_message=message_1)
        signal = SignalFactoryValidLocation(category_assignment__category=cat1)

        self.sia_read_write_user.user_permissions.add(Permission.objects.get(codename='sia_can_view_all_categories'))
        self.client.force_authenticate(user=self.sia_read_write_user)

        response = self.client.get(f'/signals/v1/private/signals/{signal.id}/history' + '?what=UPDATE_SLA')
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json[0]['description'], EMPTY_HANDLING_MESSAGE_PLACEHOLDER_MESSAGE)

    def test_history_no_permissions(self):
        """
        The sia_read_user does not have a link with any department and also is not configured with the permission
        "sia_can_view_all_categories". Therefore it should not be able to see a Signal and it's history.
        """
        self.client.force_authenticate(user=self.sia_read_write_user)
        response = self.client.get(f'/signals/v1/private/signals/{self.signal.id}/history')
        self.assertEqual(response.status_code, 403)


class TestHistoryForFeedback(SignalsBaseApiTestCase, SIAReadUserMixin):
    def setUp(self):
        self.signal = SignalFactoryValidLocation(user_assignment=None)
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
        read_user.user_permissions.add(Permission.objects.get(codename='sia_can_view_all_categories'))
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
        self.feedback.text_list = None
        self.feedback.text_extra = text_extra
        self.feedback.submitted_at = self.feedback.created_at + timedelta(days=1)
        self.feedback.save()

        # check the rendering
        read_user = self.sia_read_user
        read_user.user_permissions.add(Permission.objects.get(codename='sia_can_view_all_categories'))
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

    def test_history_no_permissions(self):
        """
        The sia_read_user does not have a link with any department and also is not configured with the permission
        "sia_can_view_all_categories". Therefore it should not be able to see a Signal and it's history.
        """
        self.client.force_authenticate(user=self.sia_read_user)
        response = self.client.get(self.history_endpoint.format(id=self.signal.id) + '?what=RECEIVE_FEEDBACK')
        self.assertEqual(response.status_code, 403)
