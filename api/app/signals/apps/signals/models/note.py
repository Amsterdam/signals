from django.contrib.gis.db import models

from signals.apps.signals.models.mixins import CreatedUpdatedModel


class Note(CreatedUpdatedModel):
    """Notes field for `Signal` instance."""
    _signal = models.ForeignKey('signals.Signal',
                                related_name='notes',
                                null=False,
                                on_delete=models.CASCADE)
    text = models.TextField(max_length=3000)
    created_by = models.EmailField(null=True, blank=True)  # analoog Priority model

    class Meta:
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['created_at']),
        ]
