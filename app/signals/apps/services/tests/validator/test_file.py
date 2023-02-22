# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from unittest.mock import Mock, patch

import pytest
from django.core.exceptions import ValidationError

from signals.apps.services.validator.file import MimeTypeAllowedValidator


class TestMimeTypeAllowedValidator:
    @patch('django.core.files.File')
    def test_validation_passes_when_mimetype_is_allowed(self, file):
        resolver = Mock(return_value='image/png')
        factory = Mock(return_value=resolver)

        validator = MimeTypeAllowedValidator(factory, ('image/png', 'image/jpeg'))
        validator(file)

    @patch('django.core.files.File')
    def test_validation_fails_when_mimetype_is_not_allowed(self, file):
        resolver = Mock(return_value='image/svg+xml')
        factory = Mock(return_value=resolver)

        validator = MimeTypeAllowedValidator(factory, ('image/png', 'image/jpeg'))
        with pytest.raises(ValidationError):
            validator(file)
