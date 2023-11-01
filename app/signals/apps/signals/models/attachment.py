# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
import logging

from django.conf import settings
from django.contrib.gis.db import models
from PIL import ImageFile

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

# Allow truncated image to be loaded:
ImageFile.LOAD_TRUNCATED_IMAGES = True


class Attachment(CreatedUpdatedModel):
    created_by = models.EmailField(null=True, blank=True)
    _signal = models.ForeignKey(
        "signals.Signal",
        null=False,
        on_delete=models.CASCADE,
        related_name='attachments',
    )
    file = models.FileField(
        upload_to='attachments/%Y/%m/%d/',
        null=False,
        blank=False,
        max_length=255,
        validators=[
            MimeTypeAllowedValidator(
                MimeTypeFromContentResolverFactory(),
                (
                    'image/jpeg',
                    'image/png',
                    'image/gif',
                    'application/pdf',
                )
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
        if self.pk is None:
            # Check if file is image
            is_image = IsImageChecker(self.file)
            self.is_image = is_image()

            if not self.mimetype and hasattr(self.file.file, 'content_type'):
                self.mimetype = self.file.file.content_type

        super().save(*args, **kwargs)
