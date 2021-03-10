# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
import logging

from django.contrib.gis.db import models
from PIL import Image, ImageFile, UnidentifiedImageError

from signals.apps.signals.models.mixins import CreatedUpdatedModel

logger = logging.getLogger(__name__)

# Allow truncated image to be loaded:
# https://github.com/matthewwithanm/django-imagekit/issues/482
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
        max_length=255
    )
    mimetype = models.CharField(max_length=30, blank=False, null=False)
    is_image = models.BooleanField(default=False)

    class Meta:
        ordering = ('created_at',)
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['is_image']),
            models.Index(fields=['_signal', 'is_image']),
        ]

    def _check_if_file_is_image(self):
        try:
            # Open the file with Pillow
            Image.open(self.file)
        except UnidentifiedImageError:
            # Raised when Pillow does not recognize an image
            return False
        return True

    def save(self, *args, **kwargs):
        if self.pk is None:
            # Check if file is image
            self.is_image = self._check_if_file_is_image()

            if not self.mimetype and hasattr(self.file.file, 'content_type'):
                self.mimetype = self.file.file.content_type

        super().save(*args, **kwargs)
