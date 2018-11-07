from django.test import TestCase

from signals.apps.zds.models import ZaakDocument, ZaakSignal
from tests.apps.signals.factories import SignalFactory
from tests.apps.zds.factories import ZaakSignalFactory, ZaakDocumentFactory


class TestZaakSignalManager(TestCase):

    def test_create_zaak_signal(self):
        self.assertEqual(ZaakSignal.objects.count(), 0)
        signal = SignalFactory()
        ZaakSignal.actions.create_zaak_signal('http://amsterdam.nl/', signal)
        self.assertEqual(ZaakSignal.objects.count(), 1)

    def test_add_document(self):
        self.assertEqual(ZaakDocument.objects.count(), 0)
        zaak_signal = ZaakSignalFactory()
        ZaakSignal.actions.add_document('http://amsterdam.nl/', zaak_signal)


class TestZaakSignal(TestCase):

    def test_str(self):
        zaak_signal = ZaakSignalFactory()
        self.assertEqual(zaak_signal.__str__(), zaak_signal.zrc_link)

    def test_document_url_no_documents(self):
        zaak_signal = ZaakSignalFactory()
        self.assertIsNone(zaak_signal.document_url)

    def test_document_url_with_documents(self):
        zaak_signal = ZaakSignalFactory()
        zaak_document = ZaakDocumentFactory(zaak_signal=zaak_signal)
        self.assertEqual(zaak_signal.document_url, zaak_document.drc_link)

    def test_document_url_with_multiple_documents(self):
        zaak_signal = ZaakSignalFactory()
        ZaakDocumentFactory(zaak_signal=zaak_signal)
        zaak_document = ZaakDocumentFactory(zaak_signal=zaak_signal)
        self.assertEqual(zaak_signal.document_url, zaak_document.drc_link)


class TestZaakDocument(TestCase):

    def test_str(self):
        zaak_document = ZaakDocumentFactory()
        self.assertEqual(zaak_document.__str__(), zaak_document.drc_link)
