# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
"""
For the DOORGEZET_NAAR_EXTERN flow Session objects are prepared each time a
Signal is transitioned to DOORGEZET_NAAR_EXTERN. These Session objects allow
external parties to answer questions from Signalen users. After a set amount of
time without an answer the Session objects should be invalidated. This script
performs that task.
"""
from django.core.management import BaseCommand

from signals.apps.questionnaires.services.forward_to_external import clean_up_forward_to_external


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        self.stdout.write('Invalidating sessions with DOORGEZET_NAAR_EXTERN that are too old.')
        n_updated = clean_up_forward_to_external()

        self.stdout.write(f'Cleaned-up {n_updated} outstanding sessions.')
