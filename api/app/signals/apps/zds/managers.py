from django.db import models, transaction


class ZaakSignalManager(models.Manager):

    def create_zaak_signal(self, url, signal):
        """
        Create a connection between a case and a signal.
        """
        from .models import ZaakSignal

        with transaction.atomic():
            zaak_signal = ZaakSignal(zrc_link=url, signal=signal)
            zaak_signal.save()

        return zaak_signal

    def add_document(self, url, zaak_signal):
        """
        Adds a link between the case and the document. Zo that it is also known in the signals app.
        """
        from .models import ZaakDocument

        with transaction.atomic():
            zaak_document = ZaakDocument(drc_link=url, zaak_signal=zaak_signal)
            zaak_document.save()

        return zaak_document

