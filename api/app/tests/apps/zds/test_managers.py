from django.test import TestCase

from signals.apps.zds.models import CaseDocument, CaseSignal
from tests.apps.signals.factories import SignalFactory
from tests.apps.zds.factories import CaseSignalFactory


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
