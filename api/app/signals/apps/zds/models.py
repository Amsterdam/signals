from django.db import models

from signals.apps.signals.models import CreatedUpdatedModel


class ZaakSignalManager(models.Manager):

    def create_zaak_signal(self, url, signal):
        """
        Create a connection between a case and a signal.
        """
        zaak_signal = ZaakSignal(zrc_link=url, signal=signal)
        zaak_signal.save()

    def add_document(self, url, zaak_signal):
        """
        Adds a link between the case and the document. Zo that it is also known in the signals app.
        """
        zaak_document = ZaakDocument(drc_link=url, zaak_signal=zaak_signal)
        zaak_document.save()


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
