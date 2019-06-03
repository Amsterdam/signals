import imghdr
import logging

from django.contrib.gis.db import models
from imagekit import ImageSpec
from imagekit.cachefiles import ImageCacheFile
from imagekit.processors import ResizeToFit
from PIL import ImageFile

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

    class NotAnImageException(Exception):
        pass

    class CroppedImage(ImageSpec):
        processors = [ResizeToFit(800, 800), ]
        format = 'JPEG'
        options = {'quality': 80}

    @property
    def image_crop(self):
        return self._crop_image()

    def _crop_image(self):
        if not self.is_image:
            raise Attachment.NotAnImageException("Attachment is not an image. Use is_image to check"
                                                 " if attachment is an image before asking for the "
                                                 "cropped version.")

        generator = Attachment.CroppedImage(source=self.file)
        cache_file = ImageCacheFile(generator)

        try:
            cache_file.generate()
        except FileNotFoundError as e:
            logger.warn("File not found when generating cache file: " + str(e))

        return cache_file

    def save(self, *args, **kwargs):
        if self.pk is None:
            # Check if file is image
            self.is_image = imghdr.what(self.file) is not None

            if not self.mimetype and hasattr(self.file.file, 'content_type'):
                self.mimetype = self.file.file.content_type

        super().save(*args, **kwargs)
