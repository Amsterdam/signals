from django.db import models

from signals.apps.signals.models import CreatedUpdatedModel

from .managers import CaseSignalManager


class CaseSignal(CreatedUpdatedModel):
    signal = models.OneToOneField(
        'signals.Signal', related_name='case', on_delete=models.CASCADE)
    zrc_link = models.URLField(null=True, blank=True)
    connected_in_external_system = models.BooleanField(default=False, blank=True)
    sync_completed = models.BooleanField(default=False, blank=True)

    objects = models.Manager()
    actions = CaseSignalManager()

    __case_cache = None
    __status_history = None

    class Meta:
        ordering = ('created_at', )

    def __str__(self):
        return self.zrc_link

    def get_case(self):
        from .tasks import get_case
        if not self.__case_cache:
            self.__case_cache = get_case(self.signal)
        return self.__case_cache

    def get_statusses(self):
        from .tasks import get_status_history, get_status_type
        if not self.__status_history:
            self.__status_history = get_status_history(self.signal)
            for state in self.__status_history:
                state['statusType'] = get_status_type(state['statusType'])
        return self.__status_history

    @property
    def document_url(self):
        if self.documents.exists():
            return self.documents.first().drc_link
        return None


class CaseStatus(CreatedUpdatedModel):
    case_signal = models.ForeignKey(
        'zds.CaseSignal', related_name='statusses', on_delete=models.CASCADE)
    status = models.OneToOneField(
        'signals.Status', related_name='case_status', on_delete=models.CASCADE, null=True)
    zrc_link = models.URLField(null=True, blank=True)

    class Meta:
        ordering = ('created_at', )

    def __str__(self):
        return self.zrc_link


class CaseDocument(CreatedUpdatedModel):
    case_signal = models.ForeignKey(
        'zds.CaseSignal', related_name='documents', on_delete=models.CASCADE)
    drc_link = models.URLField(null=True, blank=True)
    connected_in_external_system = models.BooleanField(default=False, blank=True)

    class Meta:
        ordering = ('created_at', )

    def __str__(self):
        return self.drc_link
