# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2026 Delta10 B.V.
import logging
import posixpath
from collections.abc import Iterator
from itertools import islice

from django.core.files.storage import default_storage
from django.db import transaction

from signals.apps.signals.models import Attachment

log = logging.getLogger(__name__)

ATTACHMENTS_PREFIX = 'attachments'


def _storage_name(path: str, name: str) -> str:
    """Return the full storage name for listdir's backend-specific result."""
    # AzureStorage returns the blob name, including AZURE_LOCATION when that
    # setting is configured. FileField.name, and thus Storage.delete(), expects
    # the name relative to that location.
    storage_location = str(getattr(default_storage, 'location', '')).strip('/')
    if storage_location and name.startswith(f'{storage_location}/'):
        name = name.removeprefix(f'{storage_location}/')
    if name == path or name.startswith(f'{path}/'):
        return name
    return posixpath.join(path, name)


def iter_attachment_files(path: str = ATTACHMENTS_PREFIX) -> Iterator[str]:
    """Yield all attachment files using only Django's Storage API.

    S3 returns names relative to ``path`` from ``listdir`` while Azure returns
    full blob names.  Normalising both forms here keeps callers backend agnostic.
    """
    try:
        directories, files = default_storage.listdir(path)
    except FileNotFoundError:
        # FileSystemStorage has no virtual directories: an installation without
        # any attachment uploads simply has no ``attachments`` directory yet.
        return
    yield from (_storage_name(path, file_name) for file_name in files)
    for directory in directories:
        yield from iter_attachment_files(_storage_name(path, directory))


def iter_unreferenced_attachment_files(batch_size: int = 1000) -> Iterator[str]:
    """Yield stored attachment files without an ``Attachment`` database row.

    Storage files are read in batches so the cleanup command can process a
    large container without loading all object names into memory.
    """
    attachment_files = iter_attachment_files()
    while batch := list(islice(attachment_files, batch_size)):
        referenced_files = set(
            Attachment.objects.filter(file__in=batch).values_list('file', flat=True)
        )
        yield from (file_name for file_name in batch if file_name not in referenced_files)


def delete_attachment_files(file_names: list[str]) -> int:
    """Delete the supplied files if they are still unreferenced.

    The database check is repeated here. A file with an ``Attachment`` reference must not be deleted.
    """
    deleted_count = 0
    for file_name in set(file_names):
        if not file_name:
            continue
        if Attachment.objects.filter(file=file_name).exists():
            log.warning('Not deleting attachment file %s because it is still referenced', file_name)
            continue
        try:
            default_storage.delete(file_name)
            deleted_count += 1
        except Exception:
            # The database deletion has already committed. Log the failure so the
            # cleanup command can retry it without failing the Celery task.
            log.exception('Could not delete attachment file %s', file_name)
    return deleted_count


def delete_attachment_files_after_commit(file_names: list[str]) -> None:
    """Delete files only after the transaction deleting their rows commits."""
    transaction.on_commit(lambda: delete_attachment_files(file_names))
