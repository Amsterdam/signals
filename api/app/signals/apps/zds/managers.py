from django.db import models, transaction


class CaseSignalManager(models.Manager):

    def create_case_signal(self, signal):
        """
        Create a connection between a case and a signal.
        """
        from .models import CaseSignal

        with transaction.atomic():
            case_signal = CaseSignal(signal=signal)
            case_signal.save()

        return case_signal

    def add_status(self, case_signal, status):
        """
        Adds a status to a case.
        """
        from .models import CaseStatus

        with transaction.atomic():
            case_status = CaseStatus(case_signal=case_signal, status=status)
            case_status.save()

        return case_status

    def add_document(self, case_signal):
        """
        Adds a link between the case and the document. Zo that it is also known in the signals app.
        """
        from .models import CaseDocument

        with transaction.atomic():
            case_document = CaseDocument(case_signal=case_signal)
            case_document.save()

        return case_document

    def add_zrc_link(self, url, obj):
        with transaction.atomic():
            obj.zrc_link = url
            obj.save()

        return obj

    def add_drc_link(self, url, obj):
        with transaction.atomic():
            obj.drc_link = url
            obj.save()

        return obj

    def connected_in_external_system(self, obj):
        with transaction.atomic():
            obj.connected_in_external_system = True
            obj.save()

        return obj
