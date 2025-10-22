# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2025 Gemeente Amsterdam
from datetime import datetime

from django.core.management import BaseCommand
from django.db import transaction
from django.utils.timezone import make_aware

from signals.apps.signals import workflow
from signals.apps.signals.models import Signal, Status


# Transfer Signals stuck in state VERZONDEN to AFGEHANDELD_EXTERN
class Command(BaseCommand):
    help = 'Update the state of signals based on specific criteria (dry run by default)'

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            '--start-date',
            type=str,
            required=True,
            help='Start date in the format YYYY-MM-DD HH:MM'
        )
        parser.add_argument(
            '--end-date',
            type=str,
            required=True,
            help='End date in the format YYYY-MM-DD HH:MM'
        )
        parser.add_argument(
            '--no-dry-run',
            action='store_true',
            help='If provided, the command will apply changes to the database'
        )

    def handle(self, *args, **options) -> None:

        start_date = make_aware(datetime.strptime(options['start_date'], '%Y-%m-%d %H:%M'))
        end_date = make_aware(datetime.strptime(options['end_date'], '%Y-%m-%d %H:%M'))
        dry_run = not options['no_dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('Dry run mode enabled. No changes will be saved.'))

        # Filter signals based on the criteria
        filtered_signals = Signal.objects.filter(
            status__created_at__range=(start_date, end_date),
            status__state=workflow.VERZONDEN
        )

        updated_signal_ids = []

        with transaction.atomic():
            for signal in filtered_signals:

                if not dry_run:
                    new_status = Status(
                        _signal=signal,
                        state=workflow.AFGEHANDELD_EXTERN,
                        text='Vastgelopen melding vrijgegeven zonder tussenkomst CityControl.',
                    )

                    new_status.save()
                    signal.status = new_status
                    signal.save()

                updated_signal_ids.append(signal.id)

            if updated_signal_ids:
                msg = 'Successfully updated the following IDs: {}'.format(
                    ', '.join(str(_id) for _id in updated_signal_ids)
                )
                if dry_run:
                    msg += ' (Dry run: no changes were saved)'
                self.stdout.write(self.style.SUCCESS(msg))
            else:
                self.stdout.write(self.style.WARNING('No IDs were updated.'))

        if dry_run:
            self.stdout.write(self.style.WARNING('Dry run complete. No changes were saved.'))
