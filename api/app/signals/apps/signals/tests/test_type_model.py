# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time

from signals.apps.signals.factories import SignalFactory
from signals.apps.signals.models import Type


class TestTypeModel(TestCase):
    def setUp(self):
        self.signal = SignalFactory.create(type_assignment=None)
        self.signal.types.all().delete()  # These tests should work without a type set

    def test_add_type_system_user(self):
        # No types yet
        self.assertEqual(self.signal.types.count(), 0)
        self.assertIsNone(self.signal.type_assignment)

        self.signal.type_assignment = Type.objects.create(_signal=self.signal, name=Type.SIGNAL)  # Een melding
        self.signal.save()

        # Refresh the signal from the database
        self.signal.refresh_from_db()

        self.assertEqual(self.signal.types.count(), 1)
        self.assertEqual(self.signal.types.first().name, Type.SIGNAL)
        self.assertIsNone(self.signal.types.first().created_by)
        self.assertEqual(self.signal.type_assignment.name, Type.SIGNAL)
        self.assertIsNone(self.signal.type_assignment.created_by)

    def test_add_type_user(self):
        # No types yet
        self.assertEqual(self.signal.types.count(), 0)
        self.assertIsNone(self.signal.type_assignment)

        self.signal.type_assignment = Type.objects.create(_signal=self.signal, name=Type.SIGNAL,
                                                          created_by='test@test.com')  # Een melding
        self.signal.save()

        # Refresh the signal from the database
        self.signal.refresh_from_db()

        self.assertEqual(self.signal.types.count(), 1)
        self.assertEqual(self.signal.type_assignment.name, Type.SIGNAL)
        self.assertEqual(self.signal.type_assignment.created_by, 'test@test.com')

    def test_add_types(self):
        # No types yet
        self.assertEqual(self.signal.types.count(), 0)
        self.assertIsNone(self.signal.type_assignment)

        now = timezone.now()
        with freeze_time(now - timedelta(minutes=60)):
            Type.objects.create(_signal=self.signal, name=Type.SIGNAL)  # Een melding

        with freeze_time(now - timedelta(minutes=45)):
            Type.objects.create(_signal=self.signal, name=Type.QUESTION)  # Een vraag

        with freeze_time(now - timedelta(minutes=30)):
            Type.objects.create(_signal=self.signal, name=Type.REQUEST)  # Een aanvraag

        with freeze_time(now - timedelta(minutes=15)):
            Type.objects.create(_signal=self.signal, name=Type.COMPLAINT)  # Een klacht

        with freeze_time(now):
            self.signal.type_assignment = Type.objects.create(_signal=self.signal,
                                                              name=Type.MAINTENANCE)  # Groot onderhoud
            self.signal.save()

        self.assertEqual(self.signal.types.count(), 5)

        queryset = self.signal.types.all()
        self.assertEqual(queryset[0].name, Type.MAINTENANCE)
        self.assertEqual(queryset[1].name, Type.COMPLAINT)
        self.assertEqual(queryset[2].name, Type.REQUEST)
        self.assertEqual(queryset[3].name, Type.QUESTION)
        self.assertEqual(queryset[4].name, Type.SIGNAL)

        # Currently assigned type
        self.assertEqual(self.signal.type_assignment.name, Type.MAINTENANCE)
        self.assertIsNone(self.signal.type_assignment.created_by)

    def test_add_types_order(self):
        # No types yet
        self.assertEqual(self.signal.types.count(), 0)
        self.assertIsNone(self.signal.type_assignment)

        now = timezone.now()
        with freeze_time(now - timedelta(minutes=15)):
            Type.objects.create(_signal=self.signal, name=Type.COMPLAINT)  # Een klacht

        with freeze_time(now - timedelta(minutes=45)):
            Type.objects.create(_signal=self.signal, name=Type.QUESTION)  # Een vraag

        with freeze_time(now - timedelta(minutes=30)):
            Type.objects.create(_signal=self.signal, name=Type.REQUEST)  # Een aanvraag

        with freeze_time(now - timedelta(minutes=60)):
            Type.objects.create(_signal=self.signal, name=Type.SIGNAL)  # Een melding

        with freeze_time(now):
            self.signal.type_assignment = Type.objects.create(_signal=self.signal, name=Type.MAINTENANCE,
                                                              created_by='test@test.com')  # Groot onderhoud
            self.signal.save()

        self.assertEqual(self.signal.types.count(), 5)

        queryset = self.signal.types.all()
        self.assertEqual(queryset[0].name, Type.MAINTENANCE)
        self.assertEqual(queryset[0].created_by, 'test@test.com')

        self.assertEqual(queryset[1].name, Type.COMPLAINT)
        self.assertIsNone(queryset[1].created_by)

        self.assertEqual(queryset[2].name, Type.REQUEST)
        self.assertIsNone(queryset[2].created_by)

        self.assertEqual(queryset[3].name, Type.QUESTION)
        self.assertIsNone(queryset[3].created_by)

        self.assertEqual(queryset[4].name, Type.SIGNAL)
        self.assertIsNone(queryset[4].created_by)

        # Currently assigned type
        self.assertEqual(self.signal.type_assignment.name, Type.MAINTENANCE)
        self.assertEqual(self.signal.type_assignment.created_by, 'test@test.com')
