# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from django.core.management import BaseCommand
from elasticsearch_dsl import Index


class Command(BaseCommand):
    help = 'Manage status messages index'

    def handle(self, *args, **options):
        index = Index('status_messages')
        index.delete()
