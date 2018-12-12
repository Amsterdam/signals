from django.test import TestCase

from signals.apps.zds.models import CaseDocument, CaseSignal
from tests.apps.signals.factories import SignalFactory
from tests.apps.zds.factories import CaseDocumentFactory, CaseSignalFactory


class TestCaseSignalManager(TestCase):

    def test_create_case_signal(self):
        self.assertEqual(CaseSignal.objects.count(), 0)
        signal = SignalFactory()
        CaseSignal.actions.create_case_signal(signal)
        self.assertEqual(CaseSignal.objects.count(), 1)

    def test_add_document(self):
        self.assertEqual(CaseDocument.objects.count(), 0)
        case_signal = CaseSignalFactory()
        CaseSignal.actions.add_document(case_signal)


class TestCaseSignal(TestCase):

    def test_str(self):
        case_signal = CaseSignalFactory()
        self.assertEqual(case_signal.__str__(), case_signal.zrc_link)

    def test_document_url_no_documents(self):
        case_signal = CaseSignalFactory()
        self.assertIsNone(case_signal.document_url)

    def test_document_url_with_documents(self):
        case_signal = CaseSignalFactory()
        case_document = CaseDocumentFactory(case_signal=case_signal)
        self.assertEqual(case_signal.document_url, case_document.drc_link)

    def test_document_url_with_multiple_documents(self):
        case_signal = CaseSignalFactory()
        CaseDocumentFactory(case_signal=case_signal)
        case_document = CaseDocumentFactory(case_signal=case_signal)
        self.assertEqual(case_signal.document_url, case_document.drc_link)


class TestCaseDocument(TestCase):

    def test_str(self):
        case_document = CaseDocumentFactory()
        self.assertEqual(case_document.__str__(), case_document.drc_link)
