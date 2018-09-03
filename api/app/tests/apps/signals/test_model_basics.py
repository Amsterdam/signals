"""
Tests for the model manager in signals.apps.signals.models

Note:
The need to have correctly deserialized data, creates a dependence on the serializers 
module (we need correctly deserialized data, not just JSON from our fixtures). If the
serializers are broken, these tests will stop working as well.
"""

import json
import os
import unittest
from unittest import mock

from django.conf import settings
from django.db.models import signals as django_built_in_signals
from django.dispatch import receiver
from django.test import TestCase
from factory.django import mute_signals

from signals.apps.signals.models import (
    Category,
    Location,
    Reporter,
    Signal,
    Status,
    create_initial,
    update_category,
    update_location,
    update_reporter,
    update_status
)
from signals.apps.signals.models import(
    create_initial, update_category, update_location, update_reporter, update_status)
from signals.apps.signals.serializers import SignalCreateSerializer


class TestSignalManager(TestCase):
    fixture_files = {
        "post_signal": "signal_post.json",
        "post_status": "status_auth_post.json",
        "post_category": "category_auth_post.json",
        "post_location": "location_auth_post.json",
    }

    def _get_fixture(self, name):
        filename = self.fixture_files[name]
        path = os.path.join(settings.BASE_DIR, 'apps', 'signals', 'fixtures', filename)

        with open(path) as fixture_file:
            postjson = json.loads(fixture_file.read())

        return postjson

    def _get_signal_data(self):
        data = self._get_fixture('post_signal')

        # Disable the validation of the SignalCreateSerializer as it assumes a request to
        # be present and protects against various bad user inputs which we do not have to
        # protect agains at this point (not dealing with user data). We also do not care 
        # about the the correct link between main and sub category, image sizes, etc.
        SignalCreateSerializer.validate = lambda _, x: x
        serializer = SignalCreateSerializer(data=data)
        assert serializer.is_valid()

        # Add a stand-in for the Django user.
        signal_data = serializer.validated_data
        signal_data.user = 'jan.janssen@example.com'

        status_data = signal_data.pop('status')
        category_data = signal_data.pop('category')
        reporter_data = signal_data.pop('reporter')
        location_data = signal_data.pop('location')

        return signal_data, location_data, status_data, category_data, reporter_data

    @mute_signals(django_built_in_signals.post_save)
    @mock.patch('signals.apps.signals.models.create_initial')
    def test_create_initial(self, patched_django_signal):
        signal_data, location_data, status_data, category_data, reporter_data = self._get_signal_data()

        # Create the full Signal
        Signal.actions.create_initial(
            signal_data, location_data, status_data, category_data, reporter_data)

        # Check everything is present:
        self.assertEquals(Signal.objects.count(), 1)
        self.assertEquals(Location.objects.count(), 1)
        self.assertEquals(Status.objects.count(), 1)
        self.assertEquals(Category.objects.count(), 1)
        self.assertEquals(Reporter.objects.count(), 1)

        # Check that we sent the correct Django signal
        self.assertTrue(patched_django_signal.send.called_once())

    @mute_signals(django_built_in_signals.post_save)
    @mock.patch('signals.apps.signals.models.update_location')
    def test_update_location(self, patched_django_signal):
        # Create a full signal (to be updated later)
        signal_data, location_data, status_data, category_data, reporter_data = self._get_signal_data()

        signal = Signal.actions.create_initial(
            signal_data, location_data, status_data, category_data, reporter_data)
        original_location_pk = signal.location.pk

        # Update the signal:
        location = Signal.actions.update_location(location_data, signal)

        # Check that the signal was updated in db
        self.assertNotEqual(original_location_pk, location.pk)
        self.assertEqual(Location.objects.count(), 2)

        # Check that we sent the correct Django signal
        self.assertTrue(patched_django_signal.send.called_once())

    @mute_signals(django_built_in_signals.post_save)
    @mock.patch('signals.apps.signals.models.update_status')
    def test_update_status(self, patched_django_signal):
        # Create a full signal (to be updated later)
        signal_data, location_data, status_data, category_data, reporter_data = self._get_signal_data()

        signal = Signal.actions.create_initial(
            signal_data, location_data, status_data, category_data, reporter_data)
        original_status_pk = signal.status.pk

        # Update the signal:
        status = Signal.actions.update_status(status_data, signal)

        # Check that the signal was updated in db
        self.assertNotEqual(original_status_pk, status.pk)
        self.assertEqual(Status.objects.count(), 2)

        # Check that we sent the correct Django signal
        self.assertTrue(patched_django_signal.send.called_once())

    @mute_signals(django_built_in_signals.post_save)
    @mock.patch('signals.apps.signals.models.update_category')
    def test_update_category(self, patched_django_signal):
        # Create a full signal (to be updated later)
        signal_data, location_data, status_data, category_data, reporter_data = self._get_signal_data()

        signal = Signal.actions.create_initial(
            signal_data, location_data, status_data, category_data, reporter_data)
        original_category_pk = signal.category.pk

        # Update the signal:
        category = Signal.actions.update_category(category_data, signal)

        # Check that the signal was updated in db
        self.assertNotEqual(original_category_pk, category.pk)
        self.assertEqual(Category.objects.count(), 2)

        # Check that we sent the correct Django signal
        self.assertTrue(patched_django_signal.send.called_once())

    @mute_signals(django_built_in_signals.post_save)
    @mock.patch('signals.apps.signals.models.update_reporter')
    def test_update_reporter(self, patched_signal):
        # Create a full signal (to be updated later)
        signal_data, location_data, status_data, category_data, reporter_data = self._get_signal_data()

        signal = Signal.actions.create_initial(
            signal_data, location_data, status_data, category_data, reporter_data)
        original_reporter_pk = signal.reporter.pk

        # Update the signal:
        reporter = Signal.actions.update_reporter(reporter_data, signal)

        # Check that the signal was updated in db
        self.assertNotEqual(original_reporter_pk, reporter.pk)
        self.assertEqual(Reporter.objects.count(), 2)

        self.assertTrue(patched_signal.send.called_once())

 
