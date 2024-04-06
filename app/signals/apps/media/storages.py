# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2024 Delta10 B.V.
from urllib.parse import urljoin

from django.core import signing
from django.core.files.storage import FileSystemStorage
from django.utils.encoding import filepath_to_uri

signer = signing.TimestampSigner()


class ProtectedFileSystemStorage(FileSystemStorage):
    def url(self, name):
        if self.base_url is None:
            raise ValueError("This file is not accessible via a URL.")

        url = filepath_to_uri(name)
        if url is not None:
            url = url.lstrip("/")

        signature = signer.sign(url).split(':')

        full_path = urljoin(self.base_url, url)
        return full_path + f'?t={signature[1]}&s={signature[2]}'
