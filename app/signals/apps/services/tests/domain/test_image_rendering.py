# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2026 Gemeente Amsterdam
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from django.core.files.base import ContentFile
from django.core.files.storage import InMemoryStorage
from PIL import Image

from signals.apps.services.domain import images


@pytest.mark.parametrize('size', [(16, 12), (801, 600)])
def test_historical_truncated_image_does_not_abort_rendering(size, monkeypatch, caplog):
    output = BytesIO()
    Image.new('RGB', size, 'red').save(output, format='JPEG')
    storage = InMemoryStorage()
    monkeypatch.setattr(images, 'default_storage', storage)
    attachments = []
    for index, content in enumerate((output.getvalue()[:-10], output.getvalue())):
        name = storage.save(f'synthetic-{index}.jpg', ContentFile(content))
        attachments.append(SimpleNamespace(
            pk=index, file=SimpleNamespace(name=name), created_by=None, created_at=None,
        ))
    signal = SimpleNamespace(attachments=Mock())
    signal.attachments.all.return_value = attachments

    data, names, _, _ = images.DataUriImageEncodeService.get_context_data_images(signal, 800)

    assert names == ['synthetic-1.jpg']
    assert len(data) == 1
    assert data[0].startswith('data:image/jpg;base64,')
    assert 'Cannot open image attachment' in caplog.text
