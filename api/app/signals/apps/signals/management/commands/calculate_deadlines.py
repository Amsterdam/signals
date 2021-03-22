# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
"""
This management command calculates deadlines for signals/complaints that have
no deadline. We need this to fix a problem where existing old open
signals/complaints do not show up in the punctuality filter using the
`late` of `late_factor_3` options.

Deadlines are calculated when a category is assigned. This command goes through
signals/complaints that are open that have no deadline. Each of these is
re-assigned to its category, triggering the deadline calculation and solving
the problem with the punctuality filter.
"""

from django.core.management import BaseCommand

from signals.apps.signals import workflow
from signals.apps.signals.models import CategoryAssignment, Signal

HISTORY_MESSAGE = 'Afhandel-deadline uitgerekend.'


class Command(BaseCommand):
    def _set_deadlines(self):
        # We only update the open complaints, as those are the ones that have to
        # be worked on and solved (and thus need to show up in the `punctuality`
        # filter).
        no_deadlines = Signal.objects.filter(category_assignment__deadline__isnull=True).exclude(
            status__state__in=[workflow.GESPLITST, workflow.AFGEHANDELD, workflow.GEANNULEERD]
        )

        for signal in no_deadlines.iterator(chunk_size=1000):
            category = signal.category_assignment.category

            # We have to bypass the "Actions" manager here, because it will
            # reject an update to and from the same category.
            data = {'text': HISTORY_MESSAGE, 'category': category}
            category_assignment = CategoryAssignment.objects.create(**data, _signal_id=signal.id)
            signal.category_assignment = category_assignment
            signal.save()

    def handle(self, *args, **options):
        self.stdout.write('Find open Signals without deadlines ...')
        self.stdout.write('... re-assign category (triggering deadline calculation).')

        self._set_deadlines()

        no_deadlines = Signal.objects.filter(category_assignment__deadline__isnull=True).exclude(
            status__state__in=[workflow.GESPLITST, workflow.AFGEHANDELD, workflow.GEANNULEERD]
        )
        self.stdout.write(f'Number of signals without deadlines {no_deadlines.count()}')
        self.stdout.write('Done')
