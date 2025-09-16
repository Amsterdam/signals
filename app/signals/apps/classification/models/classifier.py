from django.contrib.gis.db import models

from signals.apps.classification.utils import _get_storage_backend

class Classifier(models.Model):
    TRAINING_STATUSES = (
        ('RUNNING', 'Running'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    )

    """
    This model represents a classification model consisting of a reference to the "Main" model and a reference to the

    "Main, Sub" model
    """
    created_at = models.DateTimeField(editable=False, auto_now_add=True)

    name = models.CharField(max_length=255, null=False, blank=False)
    precision = models.FloatField(null=True, blank=True, default=0)
    recall = models.FloatField(null=True, blank=True, default=0)
    accuracy = models.FloatField(null=True, blank=True, default=0)
    is_active = models.BooleanField(default=False)
    training_status = models.CharField(default="RUNNING", choices=TRAINING_STATUSES, max_length=20)
    training_error = models.TextField(null=True, blank=True)

    main_model = models.FileField(
        upload_to='classification_models/main/%Y/%m/%d/',
        null=True,
        blank=True,
        max_length=255,
    )

    sub_model = models.FileField(
        upload_to='classification_models/main_sub/%Y/%m/%d/',
        null=True,
        blank=True,
        max_length=255,
    )

    main_confusion_matrix = models.FileField(
        upload_to='classification_models/main_confusion_matrix/%Y/%m/%d/',
        null=True,
        blank=True,
        max_length=255,
    )

    sub_confusion_matrix = models.FileField(
        upload_to='classification_models/sub_confusion_matrix/%Y/%m/%d/',
        null=True,
        blank=True,
        max_length=255,
    )