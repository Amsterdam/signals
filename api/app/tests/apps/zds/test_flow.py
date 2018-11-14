import requests_mock
from django.test import TestCase

from signals.apps.signals.models import create_initial
from tests.apps.signals.factories import SignalFactory, SignalFactoryWithImage
from tests.apps.zds.mixins import ZDSMockMixin


class TestFlows(ZDSMockMixin, TestCase):

    @requests_mock.Mocker()
    def test_complete_flow_with_image(self, mock):
        self.get_mock(mock, 'zrc_openapi')
        self.post_mock(mock, 'zrc_zaak_create')
        self.post_mock(mock, 'zrc_zaakobject_create')
        self.post_mock(mock, 'zrc_status_create')
        self.get_mock(mock, 'drc_openapi')
        self.post_mock(mock, 'drc_enkelvoudiginformatieobject_create')
        self.post_mock(mock, 'drc_objectinformatieobject_create')

        signal = SignalFactoryWithImage()

        create_initial.send(
            sender=self.__class__,
            signal_obj=signal,
        )

    @requests_mock.Mocker()
    def test_complete_flow_without_image(self, mock):
        self.get_mock(mock, 'zrc_openapi')
        self.post_mock(mock, 'zrc_zaak_create')
        self.post_mock(mock, 'zrc_zaakobject_create')
        self.post_mock(mock, 'zrc_status_create')

        signal = SignalFactory()

        create_initial.send(
            sender=self.__class__,
            signal_obj=signal,
        )

    @requests_mock.Mocker()
    def test_flow_document_not_created(self, mock):
        self.get_mock(mock, 'zrc_openapi')
        self.post_mock(mock, 'zrc_zaak_create')
        self.post_mock(mock, 'zrc_zaakobject_create')
        self.post_mock(mock, 'zrc_status_create')
        self.get_mock(mock, 'drc_openapi')
        self.post_error_mock(mock, 'drc_enkelvoudiginformatieobject_create')

        signal = SignalFactoryWithImage()

        create_initial.send(
            sender=self.__class__,
            signal_obj=signal,
        )

    @requests_mock.Mocker()
    def test_flow_zaak_not_created(self, mock):
        self.get_mock(mock, 'zrc_openapi')
        self.post_error_mock(mock, 'zrc_zaak_create')

        signal = SignalFactoryWithImage()

        create_initial.send(
            sender=self.__class__,
            signal_obj=signal,
        )
