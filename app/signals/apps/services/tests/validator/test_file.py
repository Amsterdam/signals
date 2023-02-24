# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from unittest.mock import Mock, patch

import pytest
from django.core.exceptions import ValidationError

from signals.apps.services.domain.mimetypes import MimeTypeResolvingError
from signals.apps.services.validator.file import (
    ContentIntegrityValidator,
    FileSizeValidator,
    MimeTypeAllowedValidator,
    MimeTypeIntegrityValidator
)


@patch('django.core.files.File')
class TestMimeTypeAllowedValidator:
    def test_validation_passes_when_mimetype_is_allowed(self, file):
        resolver = Mock(return_value='image/png')
        factory = Mock(return_value=resolver)

        validator = MimeTypeAllowedValidator(factory, ('image/png', 'image/jpeg'))
        validator(file)

    def test_validation_fails_when_mimetype_is_not_allowed(self, file):
        resolver = Mock(return_value='image/svg+xml')
        factory = Mock(return_value=resolver)

        validator = MimeTypeAllowedValidator(factory, ('image/png', 'image/jpeg'))
        with pytest.raises(ValidationError):
            validator(file)

    def test_validation_fails_when_mimetype_resolving_fails(self, file):
        resolver = Mock(side_effect=MimeTypeResolvingError)
        factory = Mock(return_value=resolver)

        validator = MimeTypeAllowedValidator(factory, ('image/png', 'image/jpeg'))
        with pytest.raises(ValidationError):
            validator(file)


@patch('django.core.files.File')
class TestMimeTypeIntegrityValidator:
    def test_validation_passes_when_mimetypes_match(self, file):
        mimetype_from_content_resolver = Mock(return_value='image/jpeg')
        mimetype_from_content_factory = Mock(return_value=mimetype_from_content_resolver)

        mimetype_from_filename_resolver = Mock(return_value='image/jpeg')
        mimetype_from_filename_factory = Mock(return_value=mimetype_from_filename_resolver)

        validator = MimeTypeIntegrityValidator(mimetype_from_content_factory, mimetype_from_filename_factory)
        validator(file)

    def test_validation_fails_when_mimetypes_do_not_match(self, file):
        mimetype_from_content_resolver = Mock(return_value='image/jpeg')
        mimetype_from_content_factory = Mock(return_value=mimetype_from_content_resolver)

        mimetype_from_filename_resolver = Mock(return_value='image/png')
        mimetype_from_filename_factory = Mock(return_value=mimetype_from_filename_resolver)

        validator = MimeTypeIntegrityValidator(mimetype_from_content_factory, mimetype_from_filename_factory)
        with pytest.raises(ValidationError) as e_info:
            validator(file)

        assert e_info.value.message == "'image/jpeg' does not match filename extension!"

    def test_validation_fails_when_mimetype_cannot_be_resolved_from_file_content(self, file):
        mimetype_from_content_resolver = Mock(side_effect=MimeTypeResolvingError)
        mimetype_from_content_factory = Mock(return_value=mimetype_from_content_resolver)

        mimetype_from_filename_resolver = Mock(return_value='image/png')
        mimetype_from_filename_factory = Mock(return_value=mimetype_from_filename_resolver)

        validator = MimeTypeIntegrityValidator(mimetype_from_content_factory, mimetype_from_filename_factory)
        with pytest.raises(ValidationError) as e_info:
            validator(file)

        assert e_info.value.message == "Failed to resolve mime type from file content!"

    def test_validation_fails_when_mimetype_cannot_be_resolved_from_filename(self, file):
        mimetype_from_content_resolver = Mock(return_value='image/jpeg')
        mimetype_from_content_factory = Mock(return_value=mimetype_from_content_resolver)

        mimetype_from_filename_resolver = Mock(side_effect=MimeTypeResolvingError)
        mimetype_from_filename_factory = Mock(return_value=mimetype_from_filename_resolver)

        validator = MimeTypeIntegrityValidator(mimetype_from_content_factory, mimetype_from_filename_factory)
        with pytest.raises(ValidationError) as e_info:
            validator(file)

        assert e_info.value.message == "Failed to resolve mime type from filename!"


@patch('django.core.files.File')
class TestContentIntegrityValidator:
    def test_validation_passes_when_file_checks_out(self, file):
        resolver = Mock(return_value='image/jpeg')
        resolver_factory = Mock(return_value=resolver)

        checker = Mock(return_value=True)
        checker_factory = Mock(return_value=checker)

        validator = ContentIntegrityValidator(resolver_factory, checker_factory)
        validator(file)

    def test_validation_fails_when_file_does_not_check_out(self, file):
        resolver = Mock(return_value='image/jpeg')
        resolver_factory = Mock(return_value=resolver)

        checker = Mock(return_value=False)
        checker_factory = Mock(return_value=checker)

        validator = ContentIntegrityValidator(resolver_factory, checker_factory)
        with pytest.raises(ValidationError) as e_info:
            validator(file)

        assert e_info.value.message == "File is not valid!"

    def test_validation_fails_when_mimetype_cannot_be_resolved(self, file):
        resolver = Mock(side_effect=MimeTypeResolvingError)
        resolver_factory = Mock(return_value=resolver)

        checker = Mock(return_value=True)
        checker_factory = Mock(return_value=checker)

        validator = ContentIntegrityValidator(resolver_factory, checker_factory)
        with pytest.raises(ValidationError) as e_info:
            validator(file)

        assert e_info.value.message == "Failed to resolve mime type!"


@patch('django.core.files.File', size=100)
class TestFileSizeValidator:
    def test_validation_passes_when_file_is_not_too_big(self, file):
        validator = FileSizeValidator(250)
        validator(file)

    def test_validation_fails_when_file_is_too_big(self, file):
        validator = FileSizeValidator(50)
        with pytest.raises(ValidationError):
            validator(file)
