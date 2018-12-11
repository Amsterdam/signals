from django.db import models

from signals.apps.signals.models import CreatedUpdatedModel
from .managers import CaseSignalManager


class CaseSignal(CreatedUpdatedModel):
    signal = models.OneToOneField(
        'signals.Signal', related_name='case', on_delete=models.CASCADE)
    zrc_link = models.URLField(null=True, blank=True)
    connected_in_external_system = models.BooleanField(default=False, blank=True)

    objects = models.Manager()
    actions = CaseSignalManager()

    class Meta:
        ordering = ('created_at', )

    def __str__(self):
        return self.zrc_link

    @property
    def document_url(self):
        if self.documents.exists():
            return self.documents.first().drc_link
        return None


class CaseStatus(CreatedUpdatedModel):
    case_signal = models.ForeignKey(
        'zds.CaseSignal', related_name='statusses', on_delete=models.CASCADE)
    zrc_link = models.URLField(null=True, blank=True)

    class Meta:
        ordering = ('created_at', )

    def __str__(self):
        return self.drc_link


class CaseDocument(CreatedUpdatedModel):
    case_signal = models.ForeignKey(
        'zds.CaseSignal', related_name='documents', on_delete=models.CASCADE)
    drc_link = models.URLField(null=True, blank=True)
    connected_in_external_system = models.BooleanField(default=False, blank=True)

    class Meta:
        ordering = ('created_at', )

    def __str__(self):
        return self.drc_link
