# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2025 Gemeente Amsterdam
from io import StringIO
from datetime import datetime, timedelta, timezone

from django.core.management import call_command
from django.test import TestCase

from signals.apps.signals.factories import SignalFactory
from signals.apps.signals import workflow


class TestUpdateSignals(TestCase):
    def setUp(self) -> None:
        # Create signals with different creation dates and states
        self.now = datetime.now(timezone.utc)
        self.start_date = self.now - timedelta(days=10)
        self.end_date = self.now - timedelta(days=5)

        # Signal within the date range and correct state
        self.signal_in_range = SignalFactory.create(
            status__state=workflow.VERZONDEN
        )

        self.signal_in_range.status.created_at = self.start_date + timedelta(days=1)
        self.signal_in_range.status.save()

        # Signal outside the date range
        self.signal_out_of_range = SignalFactory.create(
            status__state=workflow.VERZONDEN
        )
        self.signal_out_of_range.status.created_at = self.end_date + timedelta(days=1)
        self.signal_out_of_range.status.save()

        # Signal with a different state
        self.signal_wrong_state = SignalFactory.create(
            status__state=workflow.AFGEHANDELD_EXTERN
        )
        self.signal_wrong_state.status.created_at = self.end_date + timedelta(days=1)
        self.signal_wrong_state.status.save()

    def test_dry_run(self) -> None:
        buffer = StringIO()
        call_command(
            'free_external_sent_signals',
            '--start-date', self.start_date.strftime('%Y-%m-%d %H:%M'),
            '--end-date', self.end_date.strftime('%Y-%m-%d %H:%M'),
            stdout=buffer
        )

        output = buffer.getvalue()
        self.assertIn('Dry run mode enabled. No changes will be saved.', output)
        self.assertIn(
            f"Successfully updated the following IDs: {self.signal_in_range.id} "
            "(Dry run: no changes were saved)",
            output
        )
        
        # Ensure no changes were made to the database
        self.signal_in_range.refresh_from_db()
        self.assertEqual(self.signal_in_range.status.state, workflow.VERZONDEN)

    def test_apply_changes(self) -> None:
        buffer = StringIO()
        call_command(
            'free_external_sent_signals',
            '--start-date', self.start_date.strftime('%Y-%m-%d %H:%M'),
            '--end-date', self.end_date.strftime('%Y-%m-%d %H:%M'),
            '--no-dry-run',
            stdout=buffer
        )

        output = buffer.getvalue()
        self.assertIn(f'Successfully updated the following IDs: {self.signal_in_range.id}', output)

        # Ensure the signal's state was updated in the database
        self.signal_in_range.refresh_from_db()
        self.assertEqual(self.signal_in_range.status.state, workflow.AFGEHANDELD_EXTERN)

        # Ensure other signals were not affected
        self.signal_out_of_range.refresh_from_db()
        self.assertEqual(self.signal_out_of_range.status.state, workflow.VERZONDEN)

        self.signal_wrong_state.refresh_from_db()
        self.assertEqual(self.signal_wrong_state.status.state, workflow.AFGEHANDELD_EXTERN)
