from io import StringIO

import requests_mock
from django.core.management import call_command
from django.test import TestCase

from tests.apps.signals.factories import SignalFactory, SignalFactoryWithImage
from tests.apps.zds.mixins import ZDSMockMixin


class TestCommand(ZDSMockMixin, TestCase):
    def call_management_command(self):
        self.out = StringIO()
        self.err = StringIO()
        call_command('sync_zds', stdout=self.out, stderr=self.err)

    @requests_mock.Mocker()
    def test_no_signals(self, mock):
        self.call_management_command()
        self.assertEqual(self.out.getvalue(), '')
        self.assertEqual(self.err.getvalue(), '')

    @requests_mock.Mocker()
    def test_with_signal_no_image(self, mock):
        self.get_mock(mock, 'zrc_openapi')
        self.get_mock(mock, 'ztc_openapi')
        self.get_mock(mock, 'ztc_statustypen_list')
        self.post_mock(mock, 'zrc_zaak_create')
        self.post_mock(mock, 'zrc_zaakobject_create')
        self.post_mock(mock, 'zrc_status_create')

        signal = SignalFactory()
        self.call_management_command()
        self.assertEqual(self.out.getvalue(), '')
        self.assertEqual(self.err.getvalue(), '')
        self.assertIsNotNone(signal.case)

    @requests_mock.Mocker()
    def test_with_signal_with_image(self, mock):
        self.get_mock(mock, 'zrc_openapi')
        self.get_mock(mock, 'ztc_openapi')
        self.get_mock(mock, 'ztc_statustypen_list')
        self.post_mock(mock, 'zrc_zaak_create')
        self.post_mock(mock, 'zrc_zaakobject_create')
        self.get_mock(mock, 'drc_openapi')
        self.post_mock(mock, 'drc_enkelvoudiginformatieobject_create')
        self.post_mock(mock, 'drc_objectinformatieobject_create')
        self.post_mock(mock, 'zrc_status_create')

        signal = SignalFactoryWithImage()
        self.call_management_command()
        self.assertEqual(self.out.getvalue(), '')
        self.assertEqual(self.err.getvalue(), '')
        self.assertIsNotNone(signal.case)

    @requests_mock.Mocker()
    def test_with_signal_error(self, mock):
        self.get_mock(mock, 'zrc_openapi')
        self.get_mock(mock, 'ztc_openapi')
        self.get_mock(mock, 'ztc_statustypen_list')
        self.post_error_mock(mock, 'zrc_zaak_create')

        SignalFactoryWithImage()
        self.call_management_command()
        self.assertEqual(self.out.getvalue(), '')
        self.assertNotEqual(self.err.getvalue(), '')
