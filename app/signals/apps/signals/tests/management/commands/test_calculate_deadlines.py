# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
import datetime
from io import StringIO

from django.core.management import call_command
from freezegun import freeze_time
from rest_framework.test import APITestCase

from signals.apps.signals import workflow
from signals.apps.signals.factories import (
    CategoryFactory,
    ServiceLevelObjectiveFactory,
    SignalFactory
)
from signals.apps.signals.management.commands.calculate_deadlines import HISTORY_MESSAGE, Command
from signals.apps.signals.models import Signal
from signals.test.utils import SuperUserMixin


class TestCalculateDeadlines(APITestCase, SuperUserMixin):
    NOW = datetime.datetime(2021, 3, 22, 12, 0, 0)  # A monday
    history_endpoint = '/signals/v1/private/signals/{pk}/history'

    def setUp(self):
        # We use a category without no deadlines to create signals/complaints that
        # will have deadline set to None.
        test_cat = CategoryFactory.create(name='testcategory')

        with freeze_time(self.NOW - datetime.timedelta(days=4*7)):
            self.signal_late_open = SignalFactory.create(
                status__state=workflow.GEMELD, category_assignment__category=test_cat)
            self.signal_late_closed = SignalFactory.create(
                status__state=workflow.AFGEHANDELD, category_assignment__category=test_cat)

        # We now set a Service Level Objective for the category, so that we can
        # create some signals/complaints with a deadline set to some value other
        # than None.
        ServiceLevelObjectiveFactory.create(
            category=test_cat,
            n_days=5,
            use_calendar_days=False,
        )

        with freeze_time(self.NOW - datetime.timedelta(hours=1)):
            self.signal_punctual_open = SignalFactory.create(
                status__state=workflow.GEMELD, category_assignment__category=test_cat)
            self.signal_punctual_closed = SignalFactory.create(
                status__state=workflow.AFGEHANDELD, category_assignment__category=test_cat)

    def test_handle(self):
        """
        Test that the calculate_deadlines command updates the open complaints without deadline.
        """
        self.assertEqual(Signal.objects.count(), 4)
        no_deadlines = Signal.objects.filter(category_assignment__deadline__isnull=True)
        self.assertEqual(no_deadlines.count(), 2)

        buffer = StringIO()
        call_command('calculate_deadlines', stdout=buffer)

        # all open complaints should now have a deadline, the closed one should not
        no_deadlines = Signal.objects.filter(category_assignment__deadline__isnull=True)
        self.assertEqual(no_deadlines.count(), 1)
        self.assertEqual(no_deadlines[0].id, self.signal_late_closed.id)
        self.assertEqual(no_deadlines[0].status.state, workflow.AFGEHANDELD)

        output = buffer.getvalue()
        self.assertIn('Number of signals without deadlines 0', output)

    def test__set_deadlines(self):
        """
        Test that the calculate_deadlines command updates the open complaints without deadline.
        """
        self.assertEqual(Signal.objects.count(), 4)
        no_deadlines = Signal.objects.filter(category_assignment__deadline__isnull=True)
        self.assertEqual(no_deadlines.count(), 2)

        Command()._set_deadlines()

        # all open complaints should now have a deadline, the closed one should not
        no_deadlines = Signal.objects.filter(category_assignment__deadline__isnull=True)
        self.assertEqual(no_deadlines.count(), 1)
        self.assertEqual(no_deadlines[0].id, self.signal_late_closed.id)
        self.assertEqual(no_deadlines[0].status.state, workflow.AFGEHANDELD)

    def test__history_message(self):
        """
        Test that the history of the updated complaint contains the correct message.
        """
        self.assertEqual(Signal.objects.count(), 4)
        no_deadlines = Signal.objects.filter(category_assignment__deadline__isnull=True)
        self.assertEqual(no_deadlines.count(), 2)

        # find the signal/complaint ID that should be updated
        signal_id = self.signal_late_open.id

        buffer = StringIO()
        call_command('calculate_deadlines', stdout=buffer)

        # all open complaints should now have a deadline, the closed one should not
        no_deadlines = Signal.objects.filter(category_assignment__deadline__isnull=True)
        self.assertEqual(no_deadlines.count(), 1)

        # check that the updated signal/complaint has to category assignments in
        # its history and that the most recent one contains the correct message
        self.client.force_authenticate(user=self.superuser)
        url = self.history_endpoint.format(pk=signal_id)
        data = {'what': 'UPDATE_CATEGORY_ASSIGNMENT'}

        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(len(response_json), 2)
        self.assertEqual(response_json[0]['description'], HISTORY_MESSAGE)
