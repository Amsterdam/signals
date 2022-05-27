# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from io import StringIO

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone
from freezegun import freeze_time

from signals.apps.signals.factories import SignalFactory, StatusFactory
from signals.apps.signals.models import Signal, DeletedSignal, DeletedSignalLog
from signals.apps.signals.workflow import AFGEHANDELD, GEANNULEERD


class TestDeleteSignals(TestCase):
    def setUp(self):
        self.feature_flags = settings.FEATURE_FLAGS
        if 'DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED' not in self.feature_flags:
            self.feature_flags['DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED'] = False

    def test_call_feature_disabled(self):
        feature_flags = self.feature_flags
        feature_flags['DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED'] = False

        buffer = StringIO()
        err_buffer = StringIO()
        with override_settings(FEATURE_FLAGS=feature_flags):
            call_command('delete_signals', stdout=buffer, stderr=err_buffer)
        output = buffer.getvalue()
        err_output = err_buffer.getvalue()

        self.assertEqual(output, '')
        self.assertIn('Feature flag "DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED" is not enabled', err_output)

    def test_call_with_state_required(self):
        feature_flags = self.feature_flags
        feature_flags['DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED'] = True

        buffer = StringIO()
        err_buffer = StringIO()
        with override_settings(FEATURE_FLAGS=feature_flags):
            call_command('delete_signals', stdout=buffer, stderr=err_buffer)
        output = buffer.getvalue()
        err_output = err_buffer.getvalue()

        self.assertEqual(output, '')
        self.assertIn('State is required', err_output)

    def test_call_with_invalid_state(self):
        feature_flags = self.feature_flags
        feature_flags['DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED'] = True

        buffer = StringIO()
        err_buffer = StringIO()
        with override_settings(FEATURE_FLAGS=feature_flags):
            call_command('delete_signals', '--state=x', stdout=buffer, stderr=err_buffer)
        output = buffer.getvalue()
        err_output = err_buffer.getvalue()

        self.assertEqual(output, '')
        self.assertIn('Invalid state(s) provided "x"', err_output)

    def test_call_with_days_required(self):
        feature_flags = self.feature_flags
        feature_flags['DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED'] = True

        buffer = StringIO()
        err_buffer = StringIO()
        with override_settings(FEATURE_FLAGS=feature_flags):
            call_command('delete_signals', '--state=o,a', stdout=buffer, stderr=err_buffer)
        output = buffer.getvalue()
        err_output = err_buffer.getvalue()

        self.assertEqual(output, '')
        self.assertIn('Days is required', err_output)

    def test_call_with_invalid_days(self):
        feature_flags = self.feature_flags
        feature_flags['DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED'] = True

        buffer = StringIO()
        err_buffer = StringIO()
        with override_settings(FEATURE_FLAGS=feature_flags):
            call_command('delete_signals', '--state=o,a', '--days=100', stdout=buffer, stderr=err_buffer)
        output = buffer.getvalue()
        err_output = err_buffer.getvalue()

        self.assertEqual(output, '')
        self.assertIn('Invalid days provided "100", must be at least 365', err_output)

    def test_delete_signal(self):
        feature_flags = self.feature_flags
        feature_flags['DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED'] = True

        now = timezone.now()
        for state in [AFGEHANDELD, GEANNULEERD]:
            with freeze_time(now - timezone.timedelta(days=370)):
                signal = SignalFactory.create()
            signal_id = signal.id

            with freeze_time(now - timezone.timedelta(days=368)):
                new_status = StatusFactory.create(state=state, _signal=signal)
                signal.status = new_status
                signal.save()

            buffer = StringIO()
            with override_settings(FEATURE_FLAGS=feature_flags):
                call_command('delete_signals', f'--signal-id={signal.id}', f'--state={state}', '--days=365',
                             stdout=buffer)
            output = buffer.getvalue()

            self.assertIn(f'- Deleting signal "{signal_id}"', output)
            self.assertFalse(Signal.objects.filter(id=signal_id).exists())
            self.assertTrue(DeletedSignal.objects.filter(id=signal_id).exists())

            deleted_signal = DeletedSignal.objects.get(id=signal_id)
            self.assertEqual(DeletedSignalLog.objects.filter(deleted_signal_id=deleted_signal).count(), 1)

            deleted_signal_log = DeletedSignalLog.objects.get(deleted_signal_id=deleted_signal)

            diff = timezone.now() - signal.status.created_at
            note = f'signal was in state "{signal.status.get_state_display()}" for {diff.days} days'
            self.assertEqual(deleted_signal_log.note, note)

    def test_delete_signals(self):
        feature_flags = self.feature_flags
        feature_flags['DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED'] = True

        now = timezone.now()
        for days in range(10):
            with freeze_time(now - timezone.timedelta(days=370)):
                signal = SignalFactory.create()

            with freeze_time(now - timezone.timedelta(days=371 - days)):
                new_status = StatusFactory.create(state=AFGEHANDELD, _signal=signal)
                signal.status = new_status
                signal.save()

        signals_that_not_should_be_deleted = Signal.objects.filter(
            status__state=AFGEHANDELD, status__created_at__gt=now - timezone.timedelta(days=365)
        ).values_list('id', flat=True)

        import pdb
        pdb.set_trace()
        self.assertEqual(5, signals_that_not_should_be_deleted.count())

        signals_that_should_be_deleted = Signal.objects.filter(
            status__state=AFGEHANDELD, status__created_at__lt=now - timezone.timedelta(days=365)
        ).values_list('id', flat=True)
        self.assertEqual(5, signals_that_should_be_deleted.count())

        self.assertEqual(10, Signal.objects.count())
        self.assertEqual(0, DeletedSignal.objects.count())
        self.assertEqual(0, DeletedSignalLog.objects.count())

        buffer = StringIO()
        # with override_settings(FEATURE_FLAGS=feature_flags):
        #     call_command('delete_signals', f'--state={AFGEHANDELD}', '--days=365', stdout=buffer)
        output = buffer.getvalue()

        self.assertEqual(5, Signal.objects.count())
        self.assertEqual(5, Signal.objects.filter(id__in=signals_that_not_should_be_deleted).count())
        self.assertEqual(5, DeletedSignal.objects.count())
        self.assertEqual(5, DeletedSignalLog.objects.filter(deleted_signal__in=signals_that_should_be_deleted).count())
        self.assertEqual(5, DeletedSignalLog.objects.count())

        for signal_id in signals_that_should_be_deleted:
            self.assertIn(f'- Deleting signal "{signal_id}"', output)
