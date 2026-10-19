# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2026 Delta10 B.V.
from unittest import mock

import pytest

from signals.apps.signals.factories import AttachmentFactory, SignalFactoryWithImage
from signals.apps.signals.models import Attachment, Signal
from signals.apps.signals.services.attachments import (
    delete_attachment_files,
    iter_attachment_files,
    iter_unreferenced_attachment_files
)
from signals.apps.signals.tasks.delete_signals import delete_signal


@pytest.mark.django_db
def test_iter_unreferenced_attachment_files_only_returns_unreferenced_files():
    attachment = AttachmentFactory()
    Attachment.objects.filter(pk=attachment.pk).update(file='attachments/referenced.jpg')

    with mock.patch(
        'signals.apps.signals.services.attachments.default_storage.listdir',
        return_value=([], ['attachments/referenced.jpg', 'attachments/unreferenced.jpg']),
    ):
        assert list(iter_unreferenced_attachment_files()) == ['attachments/unreferenced.jpg']


def test_iter_attachment_files_normalizes_s3_and_azure_listdir_results():
    def listdir(path):
        if path == 'attachments':
            return ['2026'], ['attachments/azure.jpg', 's3.jpg']
        assert path == 'attachments/2026'
        return [], ['nested.jpg']

    with mock.patch(
        'signals.apps.signals.services.attachments.default_storage.listdir', side_effect=listdir
    ):
        assert list(iter_attachment_files()) == [
            'attachments/azure.jpg',
            'attachments/s3.jpg',
            'attachments/2026/nested.jpg',
        ]


def test_iter_attachment_files_removes_azure_storage_location_from_blob_name():
    with (
        mock.patch(
            'signals.apps.signals.services.attachments.default_storage.listdir',
            return_value=([], ['media/attachments/azure.jpg']),
        ),
        mock.patch(
            'signals.apps.signals.services.attachments.default_storage.location', 'media',
        ),
    ):
        assert list(iter_attachment_files()) == ['attachments/azure.jpg']


@pytest.mark.django_db
def test_delete_attachment_files_leaves_still_referenced_file_untouched():
    attachment = AttachmentFactory()
    Attachment.objects.filter(pk=attachment.pk).update(file='attachments/referenced.jpg')

    with mock.patch('signals.apps.signals.services.attachments.default_storage.delete') as delete:
        delete_attachment_files(['attachments/referenced.jpg', 'attachments/unreferenced.jpg'])

    delete.assert_called_once_with('attachments/unreferenced.jpg')


@pytest.mark.django_db(transaction=True)
def test_signal_destruction_deletes_attachment_file_after_committing():
    signal = SignalFactoryWithImage()
    attachment_file_name = signal.attachments.get().file.name

    with mock.patch('signals.apps.signals.services.attachments.default_storage.delete') as delete:
        delete_signal.run(signal.pk)

    assert not Signal.objects.filter(pk=signal.pk).exists()
    delete.assert_called_once_with(attachment_file_name)
