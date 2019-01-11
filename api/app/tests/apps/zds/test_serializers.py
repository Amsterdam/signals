from django.test import TestCase
import requests_mock
from zds_client.client import ClientError

from signals.apps.zds.api.serializers import SignalZDSSerializer
from signals.apps.signals.models import Signal

from tests.apps.signals.factories import SignalFactory
from tests.apps.zds.mixins import ZDSMockMixin
from .factories import CaseSignalFactory


class TestSignalZDSSerializer(ZDSMockMixin, TestCase):
    def test_with_no_data(self):
        serializer = SignalZDSSerializer()
        self.assertEqual(serializer.data, {})

    def test_with_signal(self):
        signal = SignalFactory()
        serializer = SignalZDSSerializer(signal)
        self.assertEqual(serializer.data, {
            'id': signal.id,
            'zds_case': {},
            'zds_statusses': [],
            'zds_images': []
        })

    @requests_mock.Mocker()
    def test_with_signal_case(self, mock):
        status_type_url = (
            'https://ref.tst.vng.cloud/ztc/api/v1/catalogussen/' +
            '8ffb11f0-c7cc-4e35-8a64-a0639aeb8f18/zaaktypen/c2f952ca-298e-488c-b1be-a87f11bd5fa2/' +
            'statustypen/70ae2e9d-73a2-4f3d-849e-e0a29ef3064e'
        )

        signal = SignalFactory()
        case_signal = CaseSignalFactory(signal=signal)
        serializer = SignalZDSSerializer(signal)

        self.get_mock(mock, 'zrc_openapi')
        self.get_mock(mock, 'zrc_zaak_read', url=case_signal.zrc_link)
        self.get_mock(mock, 'zrc_status_list')
        self.get_mock(mock, 'ztc_openapi')
        self.get_mock(mock, 'ztc_statustypen_read', url=status_type_url)
        self.get_mock(mock, 'drc_openapi')

        self.assertEqual(serializer.data, {
            'zds_case': {},
            'zds_statusses': [],
            'zds_images': [],
        })
