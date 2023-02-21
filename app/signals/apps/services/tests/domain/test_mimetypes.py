# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
import os

import pytest

from signals.apps.services.domain.mimetypes import MimeTypeFromFilenameResolver, MimeTypeFromContentResolver, \
    MimeTypeResolvingError


class TestMimeTypeFromFilenameResolver:
    @pytest.mark.parametrize(',filename,expected', [
        ('test.svg', 'image/svg+xml'),
        ('TEST.SVG', 'image/svg+xml'),
        ('TEst.SvG', 'image/svg+xml'),
        ('teST.sVg', 'image/svg+xml'),
        ('test.jpeg', 'image/jpeg'),
        ('TEST.JPEG', 'image/jpeg'),
        ('TEst.jpEG', 'image/jpeg'),
        ('teST.JPeg', 'image/jpeg'),
        ('test.jpg', 'image/jpeg'),
        ('test.JPG', 'image/jpeg'),
        ('test.jPg', 'image/jpeg'),
        ('test.jpG', 'image/jpeg'),
        ('test.png', 'image/png'),
        ('TEST.PNG', 'image/png'),
        ('test.pnG', 'image/png'),
        ('test.gif', 'image/gif'),
        ('test.GIF', 'image/gif'),
        ('test.Gif', 'image/gif'),
        ('test.pdf', 'application/pdf'),
        ('TEST.PDF', 'application/pdf'),
        ('TEST.pDF', 'application/pdf'),
        ('test.Pdf', 'application/pdf'),
    ])
    def test_resolving(self, filename, expected):
        resolver = MimeTypeFromFilenameResolver(filename)
        assert expected == resolver()

    def test_resolving_without_extension(self):
        with pytest.raises(MimeTypeResolvingError):
            resolver = MimeTypeFromFilenameResolver('test')
            resolver()
