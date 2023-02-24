# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
import pytest
from unittest.mock import patch

from signals.apps.services.domain.checker_factories import ContentCheckerFactory
from signals.apps.services.domain.images import IsImageChecker
from signals.apps.services.domain.pdf import IsPdfChecker


@patch('django.core.files.File')
class TestContentCheckerFactory:
    @pytest.mark.parametrize("mimetype", ['image/jpeg', 'image/png', 'image/gif'])
    def test_factory_produces_image_checker_for_image_mime_type(self, file, mimetype):
        factory = ContentCheckerFactory()
        checker = factory(mimetype, file)
        assert isinstance(checker, IsImageChecker)

    def test_factory_produces_pdf_checker_for_pdf_mime_type(self, file):
        factory = ContentCheckerFactory()
        checker = factory('application/pdf', file)
        assert isinstance(checker, IsPdfChecker)
