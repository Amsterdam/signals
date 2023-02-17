# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
from timeit import default_timer as timer

from django.core.management import BaseCommand

from signals.apps.sigmax.tasks import fail_stuck_sending_signals
from signals.apps.signals.workflow import TE_VERZENDEN, VERZENDEN_MISLUKT
from signals.settings import SIGMAX_SEND_FAIL_TIMEOUT_MINUTES


class Command(BaseCommand):
    def handle(self, *args, **options):
        start = timer()

        self.stdout.write(f'Add status "{VERZENDEN_MISLUKT}" to Signals that are stuck in "{TE_VERZENDEN}" '
                          f'for at least {SIGMAX_SEND_FAIL_TIMEOUT_MINUTES} minutes')
        fail_stuck_sending_signals()

        stop = timer()
        self.stdout.write(f'Time: {stop - start:.2f} second(s)')
        self.stdout.write('Done!')
