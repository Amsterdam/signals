from django.core.exceptions import ValidationError
from django.db import models

from signals.apps.signals import workflow
from signals.apps.signals.models.mixins import CreatedUpdatedModel

MAX_INSTANCES = 5  # Max instances we allow per Category/State combination


class StatusMessageTemplate(CreatedUpdatedModel):
    """
    Standaard afmeld tekst

    Voor een categorie in een status zijn er X afmeld teksten
    """

    category = models.ForeignKey(to='Category', related_name='+', on_delete=models.DO_NOTHING)
    state = models.CharField(max_length=20, choices=workflow.STATUS_CHOICES)

    title = models.CharField(max_length=255, blank=False, null=False)
    text = models.TextField()
    order = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        permissions = (
            ('sia_statusmessagetemplate_write', 'Can write StatusMessageTemplates to SIA'),
        )
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
        verbose_name = 'Standaard afmeldtekst'
        verbose_name_plural = 'Standaard afmeldteksten'

    def save(self, *args, **kwargs):
        # The default qs we need to perform our checks
        self.full_clean()
        qs = StatusMessageTemplate.objects.filter(category_id=self.category_id, state=self.state)

        if self.pk is None and qs.count() >= MAX_INSTANCES:
            msg = 'Only {} StatusMessageTemplate instances allowed per Category/State combination'
            raise ValidationError(msg.format(MAX_INSTANCES))

        # Save the instance
        super(StatusMessageTemplate, self).save(*args, **kwargs)
