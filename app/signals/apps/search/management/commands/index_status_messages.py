# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from django.core.management import BaseCommand

from signals.apps.search.transformers.status_message import transform
from signals.apps.signals.models import StatusMessage


class Command(BaseCommand):
    help = 'Index the status messages'

    def handle(self, *args, **options):
        for status_message in StatusMessage.objects.all():
            document = transform(status_message)
            document.save()
