# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from django.core.management import BaseCommand

from signals.apps.search.documents.status_message import StatusMessage


class Command(BaseCommand):
    help = 'Initialize the status messages index'

    def handle(self, *args, **options):
        StatusMessage.init()
