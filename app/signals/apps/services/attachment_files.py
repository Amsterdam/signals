# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2026 Gemeente Amsterdam
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import FileField
from django.db.models.fields.files import FieldFile

from signals.apps.services.domain.image_sanitizer import sanitize_image
from signals.apps.services.domain.mimetypes import (
    MimeTypeFromContentResolver,
    MimeTypeResolvingError
)


def sanitize_attachment(content, name=None):
    """Sanitize image bytes at attachment write boundaries; leave non-images unchanged."""
    extension = Path(name or content.name or '').suffix.lower()
    image_extension = extension in ('.jpg', '.jpeg', '.png', '.gif')
    if content.size == 0 and not image_extension:
        return content
    try:
        mimetype = MimeTypeFromContentResolver(content)()
    except MimeTypeResolvingError as exc:
        raise ValidationError('Attachment content type could not be determined.') from exc
    finally:
        content.seek(0)
    if mimetype.startswith('image/') or image_extension:
        return sanitize_image(content, settings.API_MAX_UPLOAD_SIZE)
    return content


class SanitizedAttachmentFile(FieldFile):
    def _prepare_content(self, name, content):
        return sanitize_attachment(content, name)

    def save(self, name, content, save=True):
        clean = self._prepare_content(name, content)
        return super().save(name, clean, save=save)


class SanitizedAttachmentFileField(FileField):
    attr_class = SanitizedAttachmentFile
