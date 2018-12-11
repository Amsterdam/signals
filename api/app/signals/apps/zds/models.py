from django.db import models

from signals.apps.signals.models import CreatedUpdatedModel
from .managers import ZaakSignalManager


class ZaakSignal(CreatedUpdatedModel):
    signal = models.OneToOneField(
        'signals.Signal', related_name='zaak', on_delete=models.CASCADE)
    zrc_link = models.URLField()

    objects = models.Manager()
    actions = ZaakSignalManager()

    class Meta:
        ordering = ('created_at', )

    def __str__(self):
        return self.zrc_link

    @property
    def document_url(self):
        if self.documenten.exists():
            return self.documenten.first().drc_link
        return None


class ZaakDocument(CreatedUpdatedModel):
    zaak_signal = models.ForeignKey(
        'zds.ZaakSignal', related_name='documenten', on_delete=models.CASCADE)
    drc_link = models.URLField()

    class Meta:
        ordering = ('created_at', )

    def __str__(self):
        return self.drc_link
