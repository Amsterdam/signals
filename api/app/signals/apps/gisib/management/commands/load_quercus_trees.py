# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from datetime import timedelta

from django.core.management import BaseCommand

from signals.apps.gisib.data_loaders.quercus_tree_loader import QuercusTreeLoader


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, help='X days in the past')
        parser.add_argument('--purge-table', action='store_true', dest='_purge_table',
                            help='Purge the GISIB feature table')

    def handle(self, *args, **options):
        time_delta = timedelta(days=options['days']) if options['days'] else None
        purge_table = options['_purge_table']

        loader = QuercusTreeLoader()
        loader.load(time_delta=time_delta, purge_table=purge_table)
