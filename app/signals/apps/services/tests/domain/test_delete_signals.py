# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
from django.conf import settings
from django.core.files.storage import default_storage
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone
from freezegun import freeze_time

from signals.apps.services.domain.delete_signals import SignalDeletionService
from signals.apps.signals.factories import SignalFactory, SignalFactoryWithImage
from signals.apps.signals.models import DeletedSignal, Signal
from signals.apps.signals.workflow import AFGEHANDELD, GEANNULEERD, GEMELD, GESPLITST


class TestSignalDeletionService(TestCase):
    def setUp(self):
        self.feature_flags = settings.FEATURE_FLAGS

    def test_signal_should_not_be_deleted_feature_disabled(self):
        """
        Signal created 370 days ago and the final state set 369 days ago. The feature flag is disabled. So the signals
        should not be deleted.
        """
        self.feature_flags['DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED'] = False

        with freeze_time(timezone.now() - timezone.timedelta(days=370)):
            signal = SignalFactory.create(status__state=AFGEHANDELD)

        with self.assertRaises(ValueError):
            SignalDeletionService.delete_signals(AFGEHANDELD, 365, dry_run=False)

        self.assertTrue(Signal.objects.filter(id=signal.id).exists())
        self.assertFalse(DeletedSignal.objects.filter(signal_id=signal.id).exists())

    def test_signal_should_not_be_deleted_dry_run(self):
        """
        Signal created 370 days ago and the final state set 369 days ago. The dry run flag is set. So the signal should
        not be deleted.
        """
        self.feature_flags['DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED'] = True

        with freeze_time(timezone.now() - timezone.timedelta(days=370)):
            signal = SignalFactory.create(status__state=GEANNULEERD)

        with override_settings(FEATURE_FLAGS=self.feature_flags):
            n_deleted, batch_uuid, t_taken = SignalDeletionService.delete_signals(GEANNULEERD, 365, dry_run=True)

        self.assertTrue(Signal.objects.filter(id=signal.id).exists())
        self.assertFalse(DeletedSignal.objects.filter(signal_id=signal.id).exists())
        self.assertEqual(n_deleted, 0)

    def test_signal_should_not_be_deleted(self):
        """
        Signal created 6 days ago and the final state set 5 days ago. So the signal should not be deleted.
        """
        self.feature_flags['DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED'] = True

        with freeze_time(timezone.now() - timezone.timedelta(days=6)):
            signal = SignalFactory.create(status__state=AFGEHANDELD)

        with override_settings(FEATURE_FLAGS=self.feature_flags):
            n_deleted, batch_uuid, t_taken = SignalDeletionService.delete_signals(AFGEHANDELD, 365, dry_run=False)

        self.assertTrue(Signal.objects.filter(id=signal.id).exists())
        self.assertFalse(DeletedSignal.objects.filter(signal_id=signal.id).exists())
        self.assertEqual(n_deleted, 0)

    def test_signal_should_be_deleted(self):
        """
        Signal created 370 days ago and the final state set 369 days ago. So the signal should be deleted.
        """
        self.feature_flags['DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED'] = True

        with freeze_time(timezone.now() - timezone.timedelta(days=370)):
            signal = SignalFactory.create(status__state=GEANNULEERD)

        with override_settings(FEATURE_FLAGS=self.feature_flags):
            n_deleted, batch_uuid, t_taken = SignalDeletionService.delete_signals(GEANNULEERD, 365, dry_run=False)

        self.assertFalse(Signal.objects.filter(id=signal.id).exists())
        self.assertTrue(DeletedSignal.objects.filter(signal_id=signal.id).exists())
        self.assertEqual(n_deleted, 1)

    def test_signal_should_not_be_deleted_wrong_states(self):
        """
        Signal created 370 days ago and the wrong state set 369 days ago. So the signal should be deleted.
        """
        self.feature_flags['DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED'] = True

        with freeze_time(timezone.now() - timezone.timedelta(days=370)):
            signal = SignalFactory.create(status__state=GEMELD)

        with override_settings(FEATURE_FLAGS=self.feature_flags):
            n_deleted, batch_uuid, t_taken = SignalDeletionService.delete_signals(AFGEHANDELD, 365, dry_run=False)

        self.assertTrue(Signal.objects.filter(id=signal.id).exists())
        self.assertFalse(DeletedSignal.objects.filter(signal_id=signal.id).exists())
        self.assertEqual(n_deleted, 0)

    def test_parent_and_child_signals_should_be_deleted(self):
        """
        Parent signal created 370 days ago and the final state set 369 days ago. So the signal and its children should
        be deleted.
        """
        self.feature_flags['DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED'] = True

        with freeze_time(timezone.now() - timezone.timedelta(days=370)):
            parent_signal = SignalFactory.create(status__state=GEANNULEERD)
            child_signal = SignalFactory.create(parent=parent_signal)

        with override_settings(FEATURE_FLAGS=self.feature_flags):
            n_deleted, batch_uuid, t_taken = SignalDeletionService.delete_signals(GEANNULEERD, 365, dry_run=False)

        self.assertFalse(Signal.objects.filter(id=parent_signal.id).exists())
        self.assertTrue(DeletedSignal.objects.filter(signal_id=parent_signal.id).exists())

        self.assertFalse(Signal.objects.filter(id=child_signal.id).exists())
        self.assertTrue(DeletedSignal.objects.filter(signal_id=child_signal.id).exists())
        self.assertEqual(n_deleted, 2)

    def test_signal_and_attachments_should_be_deleted(self):
        """
        Signal created 370 days ago and the final state set 369 days ago. So the signal should be deleted.
        The attachment should be deleted.
        """
        self.feature_flags['DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED'] = True

        with freeze_time(timezone.now() - timezone.timedelta(days=370)):
            signal = SignalFactoryWithImage.create(status__state=GEANNULEERD)

        attachment_file_path = signal.attachments.first().file.path
        self.assertTrue(default_storage.exists(attachment_file_path))

        with override_settings(FEATURE_FLAGS=self.feature_flags):
            n_deleted, batch_uuid, t_taken = SignalDeletionService.delete_signals(GEANNULEERD, 365, dry_run=False)

        self.assertFalse(Signal.objects.filter(id=signal.id).exists())
        self.assertTrue(DeletedSignal.objects.filter(signal_id=signal.id).exists())
        self.assertFalse(default_storage.exists(attachment_file_path))
        self.assertEqual(n_deleted, 1)

    def test_gesplits_parent_and_child_signals_should_be_deleted(self):
        """
        Parent signal created 370 days ago and the final state set 369 days ago. So the signal and its children should
        be deleted.
        """
        self.feature_flags['DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED'] = True

        with freeze_time(timezone.now() - timezone.timedelta(days=370)):
            parent_signal = SignalFactory.create(status__state=GESPLITST)
            child_signal = SignalFactory.create(parent=parent_signal)

        with override_settings(FEATURE_FLAGS=self.feature_flags):
            n_deleted, batch_uuid, t_taken = SignalDeletionService.delete_signals(GESPLITST, 365, dry_run=False)

        self.assertFalse(Signal.objects.filter(id=parent_signal.id).exists())
        self.assertTrue(DeletedSignal.objects.filter(signal_id=parent_signal.id).exists())

        self.assertFalse(Signal.objects.filter(id=child_signal.id).exists())
        self.assertTrue(DeletedSignal.objects.filter(signal_id=child_signal.id).exists())

        self.assertEqual(n_deleted, 2)
