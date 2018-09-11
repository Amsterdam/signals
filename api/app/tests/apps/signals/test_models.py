"""
Tests for the model manager in signals.apps.signals.models
"""
from unittest import mock

from django.test import TransactionTestCase
from django.utils import timezone
from django.contrib.gis.geos import Point

from signals.apps.signals.models import (
    GEMELD,
    STADSDEEL_CENTRUM,
    Category,
    Location,
    Priority,
    Reporter,
    Signal,
    Status
)
from tests.apps.signals.factories import SignalFactory


class TestSignalManager(TransactionTestCase):

    def setUp(self):
        # Deserialized data
        self.signal_data = {
            'text': 'text message',
            'text_extra': 'test message extra',
            'incident_date_start': timezone.now(),
        }
        self.location_data = {
            'geometrie': Point(4.898466, 52.361585),
            'stadsdeel': STADSDEEL_CENTRUM,
            'buurt_code': 'aaa1',
        }
        self.reporter_data = {
            'email': 'test_reporter@example.com',
            'phone': '0123456789',
        }
        self.category_data = {
            'main': 'Afval',
            'sub': 'Veeg- / zwerfvuil',
        }
        self.status_data = {
            'state': GEMELD,
            'text': 'text message',
            'user': 'test@example.com',
        }
        self.priority_data = {
            'priority': 'high'
        }

    @mock.patch('signals.apps.signals.models.create_initial', autospec=True)
    def test_create_initial(self, patched_create_initial):
        # Create the full Signal
        signal = Signal.actions.create_initial(
            self.signal_data,
            self.location_data,
            self.status_data,
            self.category_data,
            self.reporter_data)

        # Check everything is present:
        self.assertEquals(Signal.objects.count(), 1)
        self.assertEquals(Location.objects.count(), 1)
        self.assertEquals(Status.objects.count(), 1)
        self.assertEquals(Category.objects.count(), 1)
        self.assertEquals(Reporter.objects.count(), 1)

        # Check that we sent the correct Django signal
        patched_create_initial.send.assert_called_once_with(sender=Signal.actions.__class__,
                                                            signal_obj=signal)

    @mock.patch('signals.apps.signals.models.update_location', autospec=True)
    def test_update_location(self, patched_update_location):
        signal = SignalFactory.create()

        # Update the signal
        prev_location = signal.location
        location = Signal.actions.update_location(self.location_data, signal)

        # Check that the signal was updated in db
        self.assertNotEqual(prev_location.pk, location.pk)
        self.assertEqual(Location.objects.count(), 2)

        # Check that we sent the correct Django signal
        patched_update_location.send.assert_called_once_with(
            sender=Signal.actions.__class__,
            signal_obj=signal,
            location=location,
            prev_location=prev_location)

    @mock.patch('signals.apps.signals.models.update_status', autospec=True)
    def test_update_status(self, patched_update_status):
        signal = SignalFactory.create()

        # Update the signal
        prev_status = signal.status
        status = Signal.actions.update_status(self.status_data, signal)

        # Check that the signal was updated in db
        self.assertNotEqual(prev_status.pk, status.pk)
        self.assertEqual(Status.objects.count(), 2)

        # Check that we sent the correct Django signal
        patched_update_status.send.assert_called_once_with(
            sender=Signal.actions.__class__,
            signal_obj=signal,
            status=status,
            prev_status=prev_status)

    @mock.patch('signals.apps.signals.models.update_category', autospec=True)
    def test_update_category(self, patched_update_category):
        signal = SignalFactory.create()

        # Update the signal
        prev_category = signal.category
        category = Signal.actions.update_category(self.category_data, signal)

        # Check that the signal was updated in db
        self.assertNotEqual(prev_category.pk, category.pk)
        self.assertEqual(Category.objects.count(), 2)

        # Check that we sent the correct Django signal
        patched_update_category.send.assert_called_once_with(
            sender=Signal.actions.__class__,
            signal_obj=signal,
            category=category,
            prev_category=prev_category)

    @mock.patch('signals.apps.signals.models.update_reporter', autospec=True)
    def test_update_reporter(self, patched_update_reporter):
        signal = SignalFactory.create()

        # Update the signal
        prev_reporter = signal.reporter
        reporter = Signal.actions.update_reporter(self.reporter_data, signal)

        # Check that the signal was updated in db
        self.assertNotEqual(prev_reporter.pk, reporter.pk)
        self.assertEqual(Reporter.objects.count(), 2)

        patched_update_reporter.send.assert_called_once_with(
            sender=Signal.actions.__class__,
            signal_obj=signal,
            reporter=reporter,
            prev_reporter=prev_reporter)

    @mock.patch('signals.apps.signals.models.update_priority')
    def test_update_priority(self, patched_update_priority):
        signal = SignalFactory.create()

        # Update the signal
        prev_priority = signal.priority
        priority = Signal.actions.update_priority(self.priority_data, signal)

        # Check that the signal was updated in db
        self.assertNotEqual(prev_priority.pk, priority.pk)
        self.assertEqual(Priority.objects.count(), 2)

        patched_update_priority.send.assert_called_once_with(
            sender=Signal.actions.__class__,
            signal_obj=signal,
            priority=priority,
            prev_priority=prev_priority)
