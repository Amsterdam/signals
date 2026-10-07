# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2026 Delta10 B.V.
from itertools import batched

from django.core.management import BaseCommand, CommandError

from signals.apps.signals.services.attachments import (
    delete_attachment_files,
    iter_unreferenced_attachment_files
)

DELETE_BATCH_SIZE = 1000


class Command(BaseCommand):
    help = (
        'Find attachment files in storage that have no Attachment database row, '
        'and optionally remove them.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Delete unreferenced files. Without this flag, only report them.',
        )

    def handle(self, *args, **options):
        delete_files = options['delete']
        unreferenced_file_count = 0
        deleted_file_count = 0

        try:
            for file_names in batched(iter_unreferenced_attachment_files(), DELETE_BATCH_SIZE):
                unreferenced_file_count += len(file_names)
                for file_name in file_names:
                    self.stdout.write(file_name)

                if delete_files:
                    deleted_file_count += delete_attachment_files(list(file_names))
        except Exception as error:
            raise CommandError(f'Could not list attachment storage: {error}') from error

        if delete_files:
            self.stdout.write(f'Deleted {deleted_file_count} unreferenced attachment file(s).')
        else:
            self.stdout.write(
                f'Found {unreferenced_file_count} unreferenced attachment file(s). '
                'Run again with --delete to remove them.'
            )
