from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField

from signals.apps.services.domain.deadlines import DeadlineCalculationService
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

    # These deadline fields are used to track whether a Signal (complaint) is
    # handled within the allotted time. By calculating these deadlines it is
    # possible to implement filtering on punctuality. Business requirements were
    # that filtering is possible on Signals that are late or late with a factor
    # of three.
    # These are allowed to be null because the deadlines cannot be determined
    # correctly for historic data (hence no attempt is made). Furthermore, we
    # store both the deadline and the deadline delayed with a factor of three
    # because of subtleties in the way the latter is determined for workdays.
    deadline = models.DateTimeField(null=True)
    deadline_factor_3 = models.DateTimeField(null=True)

    def __str__(self):
        """String representation."""
        return '{sub} - {signal}'.format(sub=self.category, signal=self._signal)

    def save(self, *args, **kwargs):
        # Each time a category is changed the ServiceLevelObjective associated
        # with the new category may be different, de deadlines are recalculated
        # and saved for use in punctuality filter.
        # Note: this may be moved to the API layer of SIA/Signalen.
        self.deadline, self.deadline_factor_3 = DeadlineCalculationService.from_signal_and_category(
            self._signal, self.category)
        super().save(*args, **kwargs)
