# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.conf import settings
from django.core.management import BaseCommand
from django.utils import timezone

from signals.apps.signals.workflow import AFGEHANDELD, GEANNULEERD


class Command(BaseCommand):
    STATE_CHOICES = (AFGEHANDELD, GEANNULEERD, )

    def add_arguments(self, parser):
        parser.add_argument('--signal-id', type=int, dest='signal_id', help='The ID of a specific signal (optional)')
        parser.add_argument('--state', type=str, help='Comma seperated list of states a Signal needs to be in, '
                                                      f'choices are: {", ".join(self.STATE_CHOICES)} (required)')
        parser.add_argument('--days', type=int, help='Number of days a Signal needs to be in a given state(s) '
                                                     '(required)')

        parser.add_argument('--dry-run', action='store_true', dest='_dry_run', help='Dry-run mode, will only show what '
                                                                                    'would be deleted (optional)')

    def _pre_handle(self, **options):
        states = options['state'].split(',') if options['state'] else None
        if not states:
            raise ValueError('State is required')

        state_diff = set(states) - set(self.STATE_CHOICES)
        if state_diff:
            raise ValueError(f'Invalid state(s) provided "{", ".join(state_diff)}"')

        self.states = states

        days = options['days'] if options['days'] else None
        if not days:
            raise ValueError('Days is required')

        now = timezone.now()
        td = timezone.datetime(day=31, month=12, year=now.year) - timezone.datetime(day=1, month=1, year=now.year)
        if days < (td.days + 1):
            raise ValueError(f'Invalid days provided "{days}", must be at least {td.days+1}')

        self.days = days

    def handle(self, *args, **options):
        if not settings.FEATURE_FLAGS.get('DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED', False):
            self.stderr.write('Feature flag "DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED" is not enabled')
            return

        self._dry_run = options['_dry_run']

        try:
            self._pre_handle(**options)
        except ValueError as e:
            self.stderr.write(f'{e}')
            return

        signal_id = options['signal_id'] if options['signal_id'] else None
        if signal_id:
            # Run for a single Signal
            ...
        else:
            # Run on complete database
            ...
