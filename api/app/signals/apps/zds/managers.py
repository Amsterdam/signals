from django.db import models, transaction


class CaseSignalManager(models.Manager):

    def create_case_signal(self, url, signal):
        """
        Create a connection between a case and a signal.
        """
        from .models import CaseSignal

        with transaction.atomic():
            case_signal = CaseSignal(zrc_link=url, signal=signal)
            case_signal.save()

        return case_signal

    def add_status(self, url, case_signal):
        """
        Adds a status to a case.
        """
        from .models import CaseStatus

        with transaction.atomic():
            case_status = CaseStatus(zrc_link=url, case_signal=case_signal)
            case_status.save()

        return case_status

    def add_document(self, url, case_signal):
        """
        Adds a link between the case and the document. Zo that it is also known in the signals app.
        """
        from .models import CaseDocument

        with transaction.atomic():
            case_document = CaseDocument(drc_link=url, case_signal=case_signal)
            case_document.save()

        return case_document
