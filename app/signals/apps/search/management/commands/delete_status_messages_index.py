# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from django.core.management import BaseCommand
from elasticsearch_dsl import Index

from signals.apps.search.settings import app_settings


class Command(BaseCommand):
    help = 'Manage status messages index'

    def handle(self, *args, **options):
        index = Index(app_settings.CONNECTION['STATUS_MESSAGE_INDEX'])
        index.delete()
