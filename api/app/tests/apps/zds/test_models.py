import json

import requests_mock
from django.test import TestCase
from requests.exceptions import ConnectionError

from signals.apps.zds.models import CaseSignal

from tests.apps.zds.factories import CaseDocumentFactory, CaseSignalFactory, CaseStatusFactory
from tests.apps.zds.mixins import ZDSMockMixin


class TestCaseSignal(ZDSMockMixin, TestCase):

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

    @requests_mock.Mocker()
    def test_get_case(self, mock):
        case_signal = CaseSignalFactory()

        self.get_mock(mock, 'zrc_openapi')
        self.get_mock(mock, 'zrc_zaak_read', url=case_signal.zrc_link)

        self.assertEqual(case_signal.get_case(), json.loads(self.zrc_zaak_read))

    @requests_mock.Mocker()
    def test_get_case_connection_error(self, mock):
        case_signal = CaseSignalFactory()

        self.get_exception_mock(mock, 'zrc_openapi', ConnectionError)

        self.assertIsNone(case_signal.get_case())

    def test_get_case_existing_cache(self):
        case_signal = CaseSignalFactory()
        case_signal.cache_case = 'Random'
        self.assertEqual(case_signal.get_case(), 'Random')

    @requests_mock.Mocker()
    def test_get_statusses(self, mock):
        url = (
            'https://ref.tst.vng.cloud/ztc/api/v1/catalogussen/' +
            '8ffb11f0-c7cc-4e35-8a64-a0639aeb8f18/zaaktypen/c2f952ca-298e-488c-b1be-a87f11bd5fa2/' +
            'statustypen/70ae2e9d-73a2-4f3d-849e-e0a29ef3064e'
        )
        self.get_mock(mock, 'zrc_openapi')
        self.get_mock(mock, 'zrc_status_list')
        self.get_mock(mock, 'ztc_openapi')
        self.get_mock(mock, 'ztc_statustypen_read', url=url)

        case_signal = CaseSignalFactory()
        self.assertEqual(case_signal.get_statusses(), json.loads(self.ztc_statusses))

    @requests_mock.Mocker()
    def test_get_statusses_connection_error(self, mock):
        case_signal = CaseSignalFactory()
        self.get_exception_mock(mock, 'zrc_openapi', ConnectionError)
        self.assertIsNone(case_signal.get_statusses())

    def test_get_statusses_existing_cache(self):
        case_signal = CaseSignalFactory()
        case_signal.cache_status_history = 'Random'
        self.assertEqual(case_signal.get_statusses(), 'Random')

    @requests_mock.Mocker()
    def test_get_images(self, mock):
        case_signal = CaseSignalFactory()

        oio_url = (
            'https://ref.tst.vng.cloud:443/drc/api/v1/objectinformatieobjecten?object={}'.format(
                case_signal.zrc_link)
        )
        eio_url = (
            'https://ref.tst.vng.cloud/drc/api/v1/enkelvoudiginformatieobjecten/' +
            '1239d6b1-194a-4052-85c5-8c2876428531'
        )

        self.get_mock(mock, 'drc_openapi')
        self.get_mock(mock, 'drc_objectinformatieobject_list', url=oio_url)
        self.get_mock(mock, 'drc_enkelvoudiginformatieobject_read', url=eio_url)

        self.assertEqual(case_signal.get_images(), json.loads(self.drc_images))

    @requests_mock.Mocker()
    def test_get_images_connection_error(self, mock):
        case_signal = CaseSignalFactory()
        self.get_exception_mock(mock, 'drc_openapi', ConnectionError)
        self.assertIsNone(case_signal.get_images())

    def test_get_images_existing_cache(self):
        case_signal = CaseSignalFactory()
        case_signal.cache_images = 'Random'
        self.assertEqual(case_signal.get_images(), 'Random')

    @requests_mock.Mocker()
    def test_cache_per_instance(self, mock):
        case_signal = CaseSignalFactory()
        case_signal2 = CaseSignalFactory()

        self.get_mock(mock, 'zrc_openapi')
        self.get_mock(mock, 'zrc_zaak_read', url=case_signal.zrc_link)

        self.assertIsNone(case_signal.cache_case)
        self.assertIsNone(case_signal.cache_status_history)
        self.assertIsNone(case_signal.cache_images)
        self.assertIsNone(case_signal2.cache_case)
        self.assertIsNone(case_signal2.cache_status_history)
        self.assertIsNone(case_signal2.cache_images)

        case_signal.get_case()
        self.assertIsNotNone(case_signal.cache_case)
        self.assertIsNone(case_signal.cache_status_history)
        self.assertIsNone(case_signal.cache_images)
        self.assertIsNone(case_signal2.cache_case)
        self.assertIsNone(case_signal2.cache_status_history)
        self.assertIsNone(case_signal2.cache_images)

    @requests_mock.Mocker()
    def test_cache_per_instance_lifetime(self, mock):
        case_signal = CaseSignalFactory()

        self.get_mock(mock, 'zrc_openapi')
        self.get_mock(mock, 'zrc_zaak_read', url=case_signal.zrc_link)

        case_signal2 = CaseSignal.objects.get(pk=case_signal.pk)

        self.assertIsNone(case_signal.cache_case)
        self.assertIsNone(case_signal.cache_status_history)
        self.assertIsNone(case_signal.cache_images)
        self.assertIsNone(case_signal2.cache_case)
        self.assertIsNone(case_signal2.cache_status_history)
        self.assertIsNone(case_signal2.cache_images)

        case_signal.get_case()
        self.assertIsNotNone(case_signal.cache_case)
        self.assertIsNone(case_signal.cache_status_history)
        self.assertIsNone(case_signal.cache_images)
        self.assertIsNone(case_signal2.cache_case)
        self.assertIsNone(case_signal2.cache_status_history)
        self.assertIsNone(case_signal2.cache_images)


class TestCaseStatus(TestCase):

    def test_str(self):
        case_status = CaseStatusFactory()
        self.assertEqual(case_status.__str__(), case_status.zrc_link)


class TestCaseDocument(TestCase):

    def test_str(self):
        case_document = CaseDocumentFactory()
        self.assertEqual(case_document.__str__(), case_document.drc_link)
