from io import StringIO
import requests_mock
from django.core.management import call_command
from django.test import TestCase, override_settings

from signals.apps.zds.exceptions import (
    CaseConnectionException,
    CaseNotCreatedException,
    DocumentConnectionException,
    DocumentNotCreatedException,
    StatusNotCreatedException
)
from signals.apps.zds.tasks import (
    add_document_to_case,
    add_status_to_case,
    connect_signal_to_case,
    create_case,
    create_document
)
from tests.apps.signals.factories import SignalFactory, SignalFactoryWithImage
from tests.apps.zds.factories import ZaakSignalFactory
from tests.apps.zds.mixins import ZDSMockMixin


class TestCommand(ZDSMockMixin, TestCase):
    def call_management_command(self):
        self.out = StringIO()
        call_command('add_signals_to_case', stdout=self.out)

    @requests_mock.Mocker()
    def test_no_signals(self, mock):
        self.call_management_command()
        self.assertEqual(self.out.getvalue(), '')

    @requests_mock.Mocker()
    def test_with_signal_no_image(self, mock):
        self.get_mock(mock, 'zrc_openapi')
        self.post_mock(mock, 'zrc_zaak_create')
        self.post_mock(mock, 'zrc_zaakobject_create')
        self.post_mock(mock, 'zrc_status_create')

        signal = SignalFactory()
        self.call_management_command()
        self.assertEqual(self.out.getvalue(), '')
        self.assertIsNotNone(signal.zaak)

    @requests_mock.Mocker()
    def test_with_signal_with_image(self, mock):
        self.get_mock(mock, 'zrc_openapi')
        self.post_mock(mock, 'zrc_zaak_create')
        self.post_mock(mock, 'zrc_zaakobject_create')
        self.get_mock(mock, 'drc_openapi')
        self.post_mock(mock, 'drc_enkelvoudiginformatieobject_create')
        self.post_mock(mock, 'drc_objectinformatieobject_create')
        self.post_mock(mock, 'zrc_status_create')

        signal = SignalFactoryWithImage()
        self.call_management_command()
        self.assertEqual(self.out.getvalue(), '')
        self.assertIsNotNone(signal.zaak)

    @requests_mock.Mocker()
    def test_with_signal_error(self, mock):
        self.get_mock(mock, 'zrc_openapi')
        self.post_error_mock(mock, 'zrc_zaak_create')

        signal = SignalFactoryWithImage()
        self.call_management_command()
        self.assertNotEqual(self.out.getvalue(), '')
        self.assertIsNotNone(signal.zaak)
