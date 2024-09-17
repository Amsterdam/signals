from django.contrib.gis.db import models


class Classifier(models.Model):
    """
    This model represents a classification model consisting of a reference to the "Middle" model and a reference to the

    "Middle, Sub" model
    """
    created_at = models.DateTimeField(editable=False, auto_now_add=True)

    name = models.CharField(max_length=255, null=False, blank=False)
    precision = models.FloatField(null=False, blank=False, default=0)
    recall = models.FloatField(null=False, blank=False, default=0)
    accuracy = models.FloatField(null=False, blank=False, default=0)

    middle_model = models.FileField(
        upload_to='classification_models/middle/%Y/%m/%d/',
        null=False,
        blank=False,
        max_length=255,
    )

    middle_sub_model = models.FileField(
        upload_to='classification_models/middle_sub/%Y/%m/%d/',
        null=False,
        blank=False,
        max_length=255,
    )