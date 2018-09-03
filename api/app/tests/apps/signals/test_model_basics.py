import json
import os
import unittest
from unittest import mock

from django.conf import settings
from django.dispatch import receiver
from django.test import TestCase

from signals.apps.signals.models import (
    Category, Location, Reporter, Signal, Status)
from signals.apps.signals.models import(
    create_initial, update_category, update_location, update_reporter, update_status)


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
        signal_data = self._get_fixture('post_signal')

        location_data = signal_data.pop('location')
        # The Django GEOS API cannot take parsed GeoJSON (i.e. dictionaries etc.)
        # it needs the raw GeoJSON fragment, hence:
        location_data['geometrie'] = json.dumps(location_data['geometrie'])

        status_data = signal_data.pop('status')
        category_data = signal_data.pop('category')
        reporter_data = signal_data.pop('reporter')

        del reporter_data['id']

        return signal_data, location_data, status_data, category_data, reporter_data

    @mock.patch('signals.apps.signals.django_signals.tasks')
    def test_create_initial(self, mocked_tasks):
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

    @mock.patch('signals.apps.signals.django_signals.tasks')
    def test_update_location(self, patched_tasks):
        signal_data, location_data, status_data, category_data, reporter_data = self._get_signal_data()

        # Create a full signal (to be updated later)
        signal = Signal.actions.create_initial(
            signal_data, location_data, status_data, category_data, reporter_data)
        original_location_pk = signal.location.pk

        # Update the signal:
        location_data['_signal_id'] = signal.pk
        signal = Signal.actions.update_location(location_data)  # we must reassign

        # Check that the signal was updated in db
        self.assertNotEqual(original_location_pk, signal.location.pk)
        self.assertEqual(Location.objects.count(), 2)

    @mock.patch('signals.apps.signals.django_signals.tasks')
    def test_update_methods(self, mocked_tasks):
        signal_data, location_data, status_data, category_data, reporter_data = self._get_signal_data()

        # Create a full signal (to be updated later)
        signal = Signal.actions.create_initial(
            signal_data, location_data, status_data, category_data, reporter_data)
        signal_pk = signal.pk

        # manager method name, data, model, signal attribute, django signal
        to_test = [
            ('update_location', location_data, Location, 'location', update_location),
            ('update_status', status_data, Status, 'status', update_status),
            ('update_category', category_data, Category, 'category', update_category),
            ('update_reporter', reporter_data, Reporter, 'reporter', update_reporter),
        ]

        for manager_method_name, data, model, signal_attr, django_signal in to_test:
            method = getattr(Signal.actions, manager_method_name)

            # Update the signal
            data['_signal_id'] = signal_pk
            updated_signal = method(data)

            # perform checks:
            self.assertEqual(model.objects.count(), 2)
            self.assertNotEqual(
                getattr(signal, signal_attr).pk,
                getattr(updated_signal, signal_attr).pk,
            )
