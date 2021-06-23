# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
"""
For the "Reactie Melder" flow one of the requirements is that a Signal in state
REACTIE_GEVRAAGD (reaction requested, i.e. has an outstanding question)
transitions to REACTIE_ONTVANGEN (reaction received) if a set amount of time
passed.
"""
from django.core.management import BaseCommand

from signals.apps.questionnaires.services import ReactionRequestService


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        self.stdout.write('Updating status on signals with REACTIE_GEVRAAGD that are too old.')
        n_updated = ReactionRequestService.clean_up_reaction_request()

        self.stdout.write(f'Updated {n_updated} signals.')
