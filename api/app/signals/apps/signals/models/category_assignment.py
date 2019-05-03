from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField

from signals.apps.signals.models.mixins import CreatedUpdatedModel


class CategoryAssignment(CreatedUpdatedModel):
    """Many-to-Many through model for `Signal` <-> `Category`."""
    _signal = models.ForeignKey('signals.Signal',
                                on_delete=models.CASCADE,
                                related_name='category_assignments')
    category = models.ForeignKey('signals.Category',
                                 on_delete=models.CASCADE,
                                 related_name='category_assignments')
    created_by = models.EmailField(null=True, blank=True)
    text = models.CharField(max_length=10000, null=True, blank=True)

    extra_properties = JSONField(null=True)  # TODO: candidate for removal

    def __str__(self):
        """String representation."""
        return '{sub} - {signal}'.format(sub=self.category, signal=self._signal)
