from io import StringIO

import requests_mock
from django.core.management import call_command
from django.test import TestCase

from freezegun import freeze_time

from tests.apps.signals.factories import SignalFactory, SignalFactoryWithImage
from tests.apps.zds.mixins import ZDSMockMixin

from .factories import CaseDocumentFactory, CaseSignalFactory, CaseStatusFactory


class TestCommand(ZDSMockMixin, TestCase):
    def call_management_command(self):
        self.out = StringIO()
        self.err = StringIO()
        call_command('sync_zds', stdout=self.out, stderr=self.err)

    @requests_mock.Mocker()
    def test_complete_flow_successfull(self, mock):
        self.get_mock(mock, 'zrc_openapi')
        self.get_mock(mock, 'ztc_openapi')
        self.get_mock(mock, 'ztc_statustypen_list')
        self.post_mock(mock, 'zrc_zaak_create')
        self.post_mock(mock, 'zrc_zaakobject_create')
        self.get_mock(mock, 'drc_openapi')
        self.post_mock(mock, 'drc_enkelvoudiginformatieobject_create')
        self.post_mock(mock, 'drc_objectinformatieobject_create')
        self.post_mock(mock, 'zrc_status_create')

        with freeze_time("2018-01-14"):
            signal = SignalFactoryWithImage()
        self.call_management_command()
        self.assertEqual(self.out.getvalue(), '')
        self.assertEqual(self.err.getvalue(), '')
        self.assertIsNotNone(signal.case)

    @requests_mock.Mocker()
    def test_document_not_connected_to_case(self, mock):
        self.get_mock(mock, 'drc_openapi')
        self.post_mock(mock, 'drc_objectinformatieobject_create')

        with freeze_time("2018-01-14"):
            signal = SignalFactoryWithImage()
        case_signal = CaseSignalFactory(signal=signal, connected_in_external_system=True)
        CaseStatusFactory(case_signal=case_signal, status=signal.status)
        CaseDocumentFactory(case_signal=case_signal)
        self.call_management_command()
        self.assertEqual(self.out.getvalue(), '')
        self.assertEqual(self.err.getvalue(), '')

    @requests_mock.Mocker()
    def test_document_not_created(self, mock):
        self.get_mock(mock, 'drc_openapi')
        self.post_mock(mock, 'drc_enkelvoudiginformatieobject_create')
        self.post_mock(mock, 'drc_objectinformatieobject_create')

        with freeze_time("2018-01-14"):
            signal = SignalFactoryWithImage()
        case_signal = CaseSignalFactory(signal=signal, connected_in_external_system=True)
        CaseStatusFactory(case_signal=case_signal, status=signal.status)
        self.call_management_command()
        self.assertEqual(self.out.getvalue(), '')
        self.assertEqual(self.err.getvalue(), '')

    @requests_mock.Mocker()
    def test_status_not_added(self, mock):
        self.get_mock(mock, 'ztc_openapi')
        self.get_mock(mock, 'ztc_statustypen_list')
        self.get_mock(mock, 'zrc_openapi')
        self.post_mock(mock, 'zrc_status_create')

        with freeze_time("2018-01-14"):
            signal = SignalFactoryWithImage()
        case_signal = CaseSignalFactory(signal=signal, connected_in_external_system=True)
        CaseDocumentFactory(case_signal=case_signal, connected_in_external_system=True)
        self.call_management_command()
        self.assertEqual(self.out.getvalue(), '')
        self.assertEqual(self.err.getvalue(), '')

    @requests_mock.Mocker()
    def test_case_not_connected_to_signal(self, mock):
        self.get_mock(mock, 'zrc_openapi')
        self.post_mock(mock, 'zrc_zaakobject_create')

        with freeze_time("2018-01-14"):
            signal = SignalFactoryWithImage()
        case_signal = CaseSignalFactory(signal=signal, connected_in_external_system=False)
        CaseStatusFactory(case_signal=case_signal, status=signal.status)
        CaseDocumentFactory(case_signal=case_signal, connected_in_external_system=True)
        self.call_management_command()
        self.assertEqual(self.out.getvalue(), '')
        self.assertEqual(self.err.getvalue(), '')

    @requests_mock.Mocker()
    def test_only_case_created(self, mock):
        self.get_mock(mock, 'zrc_openapi')
        self.get_mock(mock, 'ztc_openapi')
        self.get_mock(mock, 'ztc_statustypen_list')
        self.post_mock(mock, 'zrc_zaak_create')
        self.post_mock(mock, 'zrc_zaakobject_create')
        self.post_mock(mock, 'zrc_status_create')
        self.get_mock(mock, 'drc_openapi')
        self.post_mock(mock, 'drc_enkelvoudiginformatieobject_create')
        self.post_mock(mock, 'drc_objectinformatieobject_create')

        with freeze_time("2018-01-14"):
            signal = SignalFactoryWithImage()
        case_signal = CaseSignalFactory(signal=signal)
        self.call_management_command()
        self.assertEqual(self.out.getvalue(), '')
        self.assertEqual(self.err.getvalue(), '')

    @requests_mock.Mocker()
    def test_case_without_image(self, mock):
        self.get_mock(mock, 'zrc_openapi')
        self.get_mock(mock, 'ztc_openapi')
        self.get_mock(mock, 'ztc_statustypen_list')
        self.post_mock(mock, 'zrc_zaak_create')
        self.post_mock(mock, 'zrc_zaakobject_create')
        self.post_mock(mock, 'zrc_status_create')

        with freeze_time("2018-01-14"):
            SignalFactory()
        self.call_management_command()
        self.assertEqual(self.out.getvalue(), '')
        self.assertEqual(self.err.getvalue(), '')

    @requests_mock.Mocker()
    def test_error_on_document_connection(self, mock):
        self.get_mock(mock, 'zrc_openapi')
        self.get_mock(mock, 'ztc_openapi')
        self.get_mock(mock, 'ztc_statustypen_list')
        self.post_mock(mock, 'zrc_zaak_create')
        self.post_mock(mock, 'zrc_zaakobject_create')
        self.post_mock(mock, 'zrc_status_create')
        self.get_mock(mock, 'drc_openapi')
        self.post_mock(mock, 'drc_enkelvoudiginformatieobject_create')
        self.post_error_mock(mock, 'drc_objectinformatieobject_create')

        with freeze_time("2018-01-14"):
            signal = SignalFactoryWithImage()
        case_signal = CaseSignalFactory(signal=signal)
        self.call_management_command()
        self.assertEqual(self.out.getvalue(), '')
        self.assertNotEqual(self.err.getvalue(), '')

    @requests_mock.Mocker()
    def test_error_on_document_creation(self, mock):
        self.get_mock(mock, 'zrc_openapi')
        self.get_mock(mock, 'ztc_openapi')
        self.get_mock(mock, 'ztc_statustypen_list')
        self.post_mock(mock, 'zrc_zaak_create')
        self.post_mock(mock, 'zrc_zaakobject_create')
        self.post_mock(mock, 'zrc_status_create')
        self.get_mock(mock, 'drc_openapi')
        self.post_error_mock(mock, 'drc_enkelvoudiginformatieobject_create')

        with freeze_time("2018-01-14"):
            signal = SignalFactoryWithImage()
        case_signal = CaseSignalFactory(signal=signal)
        self.call_management_command()
        self.assertEqual(self.out.getvalue(), '')
        self.assertNotEqual(self.err.getvalue(), '')

    @requests_mock.Mocker()
    def test_error_on_status_creation(self, mock):
        self.get_mock(mock, 'zrc_openapi')
        self.get_mock(mock, 'ztc_openapi')
        self.get_mock(mock, 'ztc_statustypen_list')
        self.post_mock(mock, 'zrc_zaak_create')
        self.post_mock(mock, 'zrc_zaakobject_create')
        self.post_error_mock(mock, 'zrc_status_create')

        with freeze_time("2018-01-14"):
            signal = SignalFactoryWithImage()
        case_signal = CaseSignalFactory(signal=signal)
        self.call_management_command()
        self.assertEqual(self.out.getvalue(), '')
        self.assertNotEqual(self.err.getvalue(), '')

    @requests_mock.Mocker()
    def test_error_on_case_connection(self, mock):
        self.get_mock(mock, 'zrc_openapi')
        self.get_mock(mock, 'ztc_openapi')
        self.get_mock(mock, 'ztc_statustypen_list')
        self.post_mock(mock, 'zrc_zaak_create')
        self.post_error_mock(mock, 'zrc_zaakobject_create')

        with freeze_time("2018-01-14"):
            signal = SignalFactoryWithImage()
        case_signal = CaseSignalFactory(signal=signal)
        self.call_management_command()
        self.assertEqual(self.out.getvalue(), '')
        self.assertNotEqual(self.err.getvalue(), '')

    @requests_mock.Mocker()
    def test_error_on_case_creation(self, mock):
        self.get_mock(mock, 'zrc_openapi')
        self.get_mock(mock, 'ztc_openapi')
        self.get_mock(mock, 'ztc_statustypen_list')
        self.post_error_mock(mock, 'zrc_zaak_create')

        with freeze_time("2018-01-14"):
            SignalFactoryWithImage()
        self.call_management_command()
        self.assertEqual(self.out.getvalue(), '')
        self.assertNotEqual(self.err.getvalue(), '')
