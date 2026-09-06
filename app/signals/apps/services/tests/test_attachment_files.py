# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2026 Gemeente Amsterdam
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from signals.apps.services.attachment_files import SanitizedAttachmentFileField, sanitize_attachment


def image_content(name='synthetic.jpg'):
    exif = Image.Exif()
    exif[271] = 'SYNTHETIC-PRIVATE-METADATA'
    buffer = BytesIO()
    Image.new('RGB', (4, 3), 'red').save(buffer, format='JPEG', exif=exif)
    return SimpleUploadedFile(name, buffer.getvalue(), content_type='image/jpeg')


@pytest.mark.parametrize('name', ['synthetic.jpg', 'synthetic.dat'])
def test_image_detection_uses_content(name):
    result = sanitize_attachment(image_content(name))
    assert b'SYNTHETIC-PRIVATE-METADATA' not in result.read()


@pytest.mark.parametrize('content', [b'', b'%PDF-1.4\nsynthetic', b'plain text'])
def test_non_images_are_unchanged(content):
    original = ContentFile(content, name='synthetic.dat')
    assert sanitize_attachment(original) is original
    assert original.read() == content


@pytest.mark.parametrize('name', ['broken.jpg', 'broken.png', 'broken.gif'])
def test_invalid_images_do_not_fall_back_to_original(name):
    with pytest.raises(ValidationError):
        sanitize_attachment(ContentFile(b'not an image', name=name))


def test_unsupported_image_does_not_fall_back_to_original():
    output = BytesIO()
    Image.new('RGB', (3, 2)).save(output, format='BMP')
    with pytest.raises(ValidationError):
        sanitize_attachment(ContentFile(output.getvalue(), name='synthetic.bmp'))


def test_fieldfile_only_passes_sanitized_bytes_to_storage():
    storage = Mock()
    storage.generate_filename.side_effect = lambda name: name
    storage.save.side_effect = lambda name, content, **kwargs: name
    field = SanitizedAttachmentFileField(storage=storage, upload_to='attachments/')
    field.set_attributes_from_name('file')
    instance = SimpleNamespace()
    file = field.attr_class(instance, field, None)

    file.save('synthetic.jpg', image_content(), save=False)

    storage.save.assert_called_once()
    saved = storage.save.call_args.args[1]
    assert b'SYNTHETIC-PRIVATE-METADATA' not in saved.read()
    assert file._committed


def test_fieldfile_never_calls_storage_for_rejected_image():
    storage = Mock()
    field = SanitizedAttachmentFileField(storage=storage)
    field.set_attributes_from_name('file')
    file = field.attr_class(SimpleNamespace(), field, None)
    with pytest.raises(ValidationError):
        file.save('broken.jpg', ContentFile(b'broken'), save=False)
    storage.save.assert_not_called()
    assert not file._committed or file.name is None
