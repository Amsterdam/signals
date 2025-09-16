from django.contrib.gis.db import models

from signals import settings
from signals.apps.classification.utils import _get_storage_backend
from signals.apps.services.domain.checker_factories import ContentCheckerFactory
from signals.apps.services.domain.mimetypes import MimeTypeFromContentResolverFactory, \
    MimeTypeFromFilenameResolverFactory
from signals.apps.services.validator.file import MimeTypeAllowedValidator, MimeTypeIntegrityValidator, \
    ContentIntegrityValidator, FileSizeValidator


class TrainingSet(models.Model):
    """
    This model represents a training set consisting of a single XLSX file, with a "Main", "Sub" and "Text" column
    """
    created_at = models.DateTimeField(editable=False, auto_now_add=True)

    name = models.CharField(max_length=255, null=False, blank=False)

    file = models.FileField(
        upload_to='training_sets/%Y/%m/%d/',
        null=False,
        blank=False,
        max_length=255,
        validators=[
            MimeTypeAllowedValidator(
                MimeTypeFromContentResolverFactory(),
                (
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
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

