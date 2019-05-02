from django.core.exceptions import ValidationError
from django.db import models

from signals.apps.signals import workflow
from signals.apps.signals.models.mixins import CreatedUpdatedModel


class Text(CreatedUpdatedModel):
    """
    Standaard afmeld tekst

    Voor een categorie in een status zijn er X afmeld teksten
    """

    category = models.ForeignKey(to='Category', related_name='+', on_delete=models.DO_NOTHING)
    state = models.CharField(max_length=20, choices=workflow.STATUS_CHOICES)

    text = models.TextField()
    order = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        index_together = (
            'category',
            'state',
            'order',
        )
        ordering = (
            'category',
            'state',
            'order',
        )

    def save(self, *args, **kwargs):
        # The default qs we need to perform our checks
        qs = Text.objects.filter(category_id=self.category_id, state=self.state)

        max_instances = 5  # Max instances we allow per Category/State combination
        if self.pk is None and qs.count() >= max_instances:
            raise ValidationError(
                'Only {} Text instances are allowed per Category/State combination'.format(
                    max_instances
                )
            )

        # Save the instance
        super(Text, self).save(*args, **kwargs)
