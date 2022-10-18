# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.core.management.base import BaseCommand

from signals.apps.my_signals.tasks import delete_expired_tokens


class Command(BaseCommand):
    help = 'Cleanup expired tokens'

    def handle(self, *args, **options):
        delete_expired_tokens()
        self.stdout.write('Deleted expired tokens')
