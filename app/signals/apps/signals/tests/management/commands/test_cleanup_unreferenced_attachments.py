# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2026 Delta10 B.V.
from io import StringIO
from unittest import mock

from django.core.management import call_command


def test_cleanup_unreferenced_attachments_reports_unreferenced_files_by_default():
    out = StringIO()
    with mock.patch(
        'signals.apps.signals.management.commands.cleanup_unreferenced_attachments.iter_unreferenced_attachment_files',
        return_value=iter(['attachments/unreferenced.jpg']),
    ) as files:
        call_command('cleanup_unreferenced_attachments', stdout=out)

    files.assert_called_once_with()
    assert 'attachments/unreferenced.jpg' in out.getvalue()
    assert 'Found 1 unreferenced attachment file(s).' in out.getvalue()


def test_cleanup_unreferenced_attachments_deletes_unreferenced_files_only_when_requested():
    out = StringIO()
    with (
        mock.patch(
            'signals.apps.signals.management.commands.cleanup_unreferenced_attachments.'
            'iter_unreferenced_attachment_files',
            return_value=iter(['attachments/unreferenced.jpg']),
        ),
        mock.patch(
            'signals.apps.signals.management.commands.cleanup_unreferenced_attachments.delete_attachment_files',
            return_value=1,
        ) as delete,
    ):
        call_command('cleanup_unreferenced_attachments', '--delete', stdout=out)

    delete.assert_called_once_with(['attachments/unreferenced.jpg'])
    assert 'Deleted 1 unreferenced attachment file(s).' in out.getvalue()
