# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2026 Gemeente Amsterdam
import logging

from django.conf import settings
from django.contrib.gis.db import models
from django.db.models.fields.files import FieldFile

from signals.apps.services.attachment_files import SanitizedAttachmentFile, SanitizedAttachmentFileField
from signals.apps.services.domain.checker_factories import ContentCheckerFactory
from signals.apps.services.domain.images import IsImageChecker
from signals.apps.services.domain.mimetypes import (
    MimeTypeFromContentResolverFactory,
    MimeTypeFromFilenameResolverFactory
)
from signals.apps.services.validator.file import (
    ContentIntegrityValidator,
    FileSizeValidator,
    MimeTypeAllowedValidator,
    MimeTypeIntegrityValidator
)
from signals.apps.signals.models.mixins import CreatedUpdatedModel

logger = logging.getLogger(__name__)

IMAGE_MIME_TYPES = (
    'image/jpeg',
    'image/png',
    'image/gif',
)

# We allow adding PDF's as attachments for authenticated users only
PRIVATE_ALLOWED_MIME_TYPES = (
    *IMAGE_MIME_TYPES,
    'application/pdf',
)


class SignalAttachmentFile(SanitizedAttachmentFile):
    def _prepare_content(self, name, content):
        # FieldFile.save() may write before model.save(), including replacement files.
        clean = super()._prepare_content(name, content)
        self.instance.is_image = IsImageChecker(clean)()
        self.instance.mimetype = MimeTypeFromContentResolverFactory()(clean)() if clean.size else ''
        clean.seek(0)
        return clean


class SignalAttachmentFileField(SanitizedAttachmentFileField):
    attr_class = SignalAttachmentFile


class Attachment(CreatedUpdatedModel):
    created_by = models.EmailField(null=True, blank=True)
    _signal = models.ForeignKey(
        "signals.Signal",
        null=False,
        on_delete=models.CASCADE,
        related_name='attachments',
    )
    file = SignalAttachmentFileField(
        upload_to='attachments/%Y/%m/%d/',
        null=False,
        blank=False,
        max_length=255,
        validators=[
            MimeTypeAllowedValidator(
                MimeTypeFromContentResolverFactory(),
                PRIVATE_ALLOWED_MIME_TYPES,
            ),
            MimeTypeIntegrityValidator(
                MimeTypeFromContentResolverFactory(),
                MimeTypeFromFilenameResolverFactory()
            ),
            ContentIntegrityValidator(MimeTypeFromContentResolverFactory(), ContentCheckerFactory()),
            FileSizeValidator(settings.API_MAX_UPLOAD_SIZE),
        ],
    )
    mimetype = models.CharField(max_length=30, blank=False, null=False)
    is_image = models.BooleanField(default=False)

    public = models.BooleanField(default=False)
    caption = models.CharField(max_length=255, null=True)

    class Meta:
        ordering = ('created_at',)
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['is_image']),
            models.Index(fields=['_signal', 'is_image']),
        ]
        permissions = [
            ('sia_add_attachment', 'Kan bijlage aan een melding toevoegen.'),
            ('sia_change_attachment', 'Kan gegevens van een bijlage bewerken.'),
            ('sia_delete_attachment_of_normal_signal', 'Kan bijlage bij standaard melding verwijderen.'),
            ('sia_delete_attachment_of_parent_signal', 'Kan bijlage bij hoofdmelding verwijderen.'),
            ('sia_delete_attachment_of_child_signal',  'Kan bijlage bij deelmelding verwijderen.'),
            ('sia_delete_attachment_of_other_user', 'Kan bijlage bij melding van andere gebruiker verwijderen.'),
            ('sia_delete_attachment_of_anonymous_user', 'Kan bijlage toegevoegd door melder verwijderen.')
        ]

    def save(self, *args, **kwargs):
        update_fields = kwargs.get('update_fields')
        if isinstance(self.file, FieldFile) and not self.file._committed:
            if update_fields is not None and 'file' in update_fields:
                kwargs['update_fields'] = set(update_fields) | {'is_image', 'mimetype'}
        elif self.pk is None:
            self.is_image = IsImageChecker(self.file)()
            if not self.mimetype and hasattr(self.file.file, 'content_type'):
                self.mimetype = self.file.file.content_type
        super().save(*args, **kwargs)
