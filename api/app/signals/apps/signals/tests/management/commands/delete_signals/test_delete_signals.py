# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from io import StringIO

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone
from freezegun import freeze_time

from signals.apps.signals.factories import SignalFactory
from signals.apps.signals.models import DeletedSignal, Signal
from signals.apps.signals.workflow import AFGEHANDELD, GEANNULEERD, GEMELD


class TestDeleteSignals(TestCase):
    def setUp(self):
        self.feature_flags = settings.FEATURE_FLAGS

    def test_signals_should_not_be_deleted_feature_disabled(self):
        """
        Signal created 370 days ago and the final state set 369 days ago. The feature flag is disabled. So the signals
        should not be deleted.
        """
        self.feature_flags['DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED'] = False

        with freeze_time(timezone.now() - timezone.timedelta(days=370)):
            signal = SignalFactory.create(status__state=AFGEHANDELD)

        buffer = StringIO()
        with override_settings(FEATURE_FLAGS=self.feature_flags):
            call_command('delete_signals', AFGEHANDELD, '365', stdout=buffer)
        output = buffer.getvalue()

        self.assertNotIn(f'Deleted Signal: #{signal.id}', output)
        self.assertTrue(Signal.objects.filter(id=signal.id).exists())
        self.assertFalse(DeletedSignal.objects.filter(signal_id=signal.id).exists())

    def test_signals_should_not_be_deleted_dry_run(self):
        """
        Signal created 370 days ago and the final state set 369 days ago. The dry run flag is set. So the signals should
        not be deleted.
        """
        self.feature_flags['DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED'] = True

        with freeze_time(timezone.now() - timezone.timedelta(days=370)):
            signal = SignalFactory.create(status__state=GEANNULEERD)

        buffer = StringIO()
        with override_settings(FEATURE_FLAGS=self.feature_flags):
            call_command('delete_signals', GEANNULEERD, '365', '--dry-run', stdout=buffer)
        output = buffer.getvalue()

        self.assertIn(f'Deleted Signal: #{signal.id} (dry-run)', output)
        self.assertTrue(Signal.objects.filter(id=signal.id).exists())
        self.assertFalse(DeletedSignal.objects.filter(signal_id=signal.id).exists())

    def test_signals_should_not_be_deleted(self):
        """
        Signal created 6 days ago and the final state set 5 days ago. So the signals should not be deleted.
        """
        self.feature_flags['DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED'] = True

        with freeze_time(timezone.now() - timezone.timedelta(days=6)):
            signal = SignalFactory.create(status__state=AFGEHANDELD)

        buffer = StringIO()
        with override_settings(FEATURE_FLAGS=self.feature_flags):
            call_command('delete_signals', AFGEHANDELD, '365', stdout=buffer)
        output = buffer.getvalue()

        self.assertNotIn(f'Deleted Signal: #{signal.id}', output)
        self.assertTrue(Signal.objects.filter(id=signal.id).exists())
        self.assertFalse(DeletedSignal.objects.filter(signal_id=signal.id).exists())

    def test_signals_should_be_deleted(self):
        """
        Signal created 370 days ago and the final state set 369 days ago. So the signals should be deleted.
        """
        self.feature_flags['DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED'] = True

        with freeze_time(timezone.now() - timezone.timedelta(days=370)):
            signal = SignalFactory.create(status__state=GEANNULEERD)

        buffer = StringIO()
        with override_settings(FEATURE_FLAGS=self.feature_flags):
            call_command('delete_signals', GEANNULEERD, '365', stdout=buffer)
        output = buffer.getvalue()

        self.assertIn(f'Deleted Signal: #{signal.id}', output)
        self.assertFalse(Signal.objects.filter(id=signal.id).exists())
        self.assertTrue(DeletedSignal.objects.filter(signal_id=signal.id).exists())

    def test_signals_should_not_be_deleted_wrong_states(self):
        """
        Signal created 370 days ago and the wrong state set 369 days ago. So the signals should be deleted.
        """
        self.feature_flags['DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED'] = True

        with freeze_time(timezone.now() - timezone.timedelta(days=370)):
            signal = SignalFactory.create(status__state=GEMELD)

        buffer = StringIO()
        with override_settings(FEATURE_FLAGS=self.feature_flags):
            call_command('delete_signals', AFGEHANDELD, '365', stdout=buffer)
        output = buffer.getvalue()

        self.assertNotIn(f'Deleted Signal: #{signal.id}', output)
        self.assertTrue(Signal.objects.filter(id=signal.id).exists())
        self.assertFalse(DeletedSignal.objects.filter(signal_id=signal.id).exists())

    def test_parent_and_child_signals_should_be_deleted(self):
        """
        Parent signal created 370 days ago and the final state set 369 days ago. So the signal and its children should
        be deleted.
        """
        self.feature_flags['DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED'] = True

        with freeze_time(timezone.now() - timezone.timedelta(days=370)):
            parent_signal = SignalFactory.create(status__state=GEANNULEERD)
            child_signal = SignalFactory.create(parent=parent_signal)

        buffer = StringIO()
        with override_settings(FEATURE_FLAGS=self.feature_flags):
            call_command('delete_signals', GEANNULEERD, '365', stdout=buffer)
        output = buffer.getvalue()

        self.assertIn(f'Deleted Signal: #{parent_signal.id}', output)
        self.assertFalse(Signal.objects.filter(id=parent_signal.id).exists())
        self.assertTrue(DeletedSignal.objects.filter(signal_id=parent_signal.id).exists())

        self.assertIn(f'Deleted Signal: #{child_signal.id}', output)
        self.assertFalse(Signal.objects.filter(id=child_signal.id).exists())
        self.assertTrue(DeletedSignal.objects.filter(signal_id=child_signal.id).exists())
