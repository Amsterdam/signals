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
        enkelvoudiginformatieobject_url = (
            'https://ref.tst.vng.cloud/drc/api/v1/enkelvoudiginformatieobjecten/' +
            '1239d6b1-194a-4052-85c5-8c2876428531'
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
        self.get_mock(mock, 'drc_objectinformatieobject_list')
        self.get_mock(mock, 'drc_objectinformatieobject_list', url=enkelvoudiginformatieobject_url)

        self.assertEqual(serializer.data, {
            'id': signal.id,
            'zds_case': {
                'url': 'http://example.com',
                'identificatie': 'string',
                'bronorganisatie': 'string',
                'omschrijving': 'string',
                'zaaktype': 'http://example.com',
                'registratiedatum': '2018-11-14',
                'verantwoordelijkeOrganisatie': 'http://example.com',
                'startdatum': '2018-11-14',
                'einddatum': '2018-11-14',
                'einddatumGepland': '2018-11-14',
                'uiterlijkeEinddatumAfdoening': '2018-11-14',
                'toelichting': 'string',
                'zaakgeometrie': {
                    'type': 'Point',
                    'coordinates': [0, 0]
                },
                'status': 'http://example.com',
                'kenmerken': [{
                    'kenmerk': 'string',
                    'bron': 'string'
                }]
            },
            'zds_statusses': [{
                'url': 'http://example.com',
                'zaak': 'http://example.com',
                'statusType': {
                    'url': 'http://example.com',
                    'omschrijving': 'Gemeld',
                    'omschrijvingGeneriek': 'string',
                    'statustekst': 'string',
                    'isVan': 'http://example.com',
                    'volgnummer': 1,
                    'isEindstatus': True
                },
                'datumStatusGezet': '2018-11-20T10:34:43Z',
                'statustoelichting': 'string'
            }],
            'zds_images': [{
                'url': 'http://example.com',
                'informatieobject': [{
                    'url': 'http://example.com',
                    'informatieobject': 'https://ref.tst.vng.cloud/drc/api/v1/enkelvoudiginformatieobjecten/1239d6b1-194a-4052-85c5-8c2876428531',
                    'object': 'http://example.com',
                    'objectType': 'besluit',
                    'aardRelatieWeergave': 'Hoort bij, omgekeerd: kent',
                    'titel': 'string',
                    'beschrijving': 'string',
                    'registratiedatum': '2018-11-20T10:32:25Z'
                }],
                'object': 'http://example.com',
                'objectType': 'besluit',
                'aardRelatieWeergave': 'Hoort bij, omgekeerd: kent',
                'titel': 'string',
                'beschrijving': 'string',
                'registratiedatum': '2018-11-20T10:32:25Z'
            }]
        })

    @requests_mock.Mocker()
    def test_with_signal_case_case_error(self, mock):
        status_type_url = (
            'https://ref.tst.vng.cloud/ztc/api/v1/catalogussen/' +
            '8ffb11f0-c7cc-4e35-8a64-a0639aeb8f18/zaaktypen/c2f952ca-298e-488c-b1be-a87f11bd5fa2/' +
            'statustypen/70ae2e9d-73a2-4f3d-849e-e0a29ef3064e'
        )
        enkelvoudiginformatieobject_url = (
            'https://ref.tst.vng.cloud/drc/api/v1/enkelvoudiginformatieobjecten/' +
            '1239d6b1-194a-4052-85c5-8c2876428531'
        )

        signal = SignalFactory()
        case_signal = CaseSignalFactory(signal=signal)
        serializer = SignalZDSSerializer(signal)

        self.get_mock(mock, 'zrc_openapi')
        self.get_exception_mock(mock, 'zrc_zaak_read', ClientError, url=case_signal.zrc_link)
        self.get_mock(mock, 'zrc_status_list')
        self.get_mock(mock, 'ztc_openapi')
        self.get_mock(mock, 'ztc_statustypen_read', url=status_type_url)
        self.get_mock(mock, 'drc_openapi')
        self.get_mock(mock, 'drc_objectinformatieobject_list')
        self.get_mock(mock, 'drc_objectinformatieobject_list', url=enkelvoudiginformatieobject_url)

        self.assertEqual(serializer.data, {
            'id': signal.id,
            'zds_case': {},
            'zds_statusses': [{
                'url': 'http://example.com',
                'zaak': 'http://example.com',
                'statusType': {
                    'url': 'http://example.com',
                    'omschrijving': 'Gemeld',
                    'omschrijvingGeneriek': 'string',
                    'statustekst': 'string',
                    'isVan': 'http://example.com',
                    'volgnummer': 1,
                    'isEindstatus': True
                },
                'datumStatusGezet': '2018-11-20T10:34:43Z',
                'statustoelichting': 'string'
            }],
            'zds_images': [{
                'url': 'http://example.com',
                'informatieobject': [{
                    'url': 'http://example.com',
                    'informatieobject': 'https://ref.tst.vng.cloud/drc/api/v1/enkelvoudiginformatieobjecten/1239d6b1-194a-4052-85c5-8c2876428531',
                    'object': 'http://example.com',
                    'objectType': 'besluit',
                    'aardRelatieWeergave': 'Hoort bij, omgekeerd: kent',
                    'titel': 'string',
                    'beschrijving': 'string',
                    'registratiedatum': '2018-11-20T10:32:25Z'
                }],
                'object': 'http://example.com',
                'objectType': 'besluit',
                'aardRelatieWeergave': 'Hoort bij, omgekeerd: kent',
                'titel': 'string',
                'beschrijving': 'string',
                'registratiedatum': '2018-11-20T10:32:25Z'
            }]
        })

    @requests_mock.Mocker()
    def test_with_signal_case_status_error(self, mock):
        status_type_url = (
            'https://ref.tst.vng.cloud/ztc/api/v1/catalogussen/' +
            '8ffb11f0-c7cc-4e35-8a64-a0639aeb8f18/zaaktypen/c2f952ca-298e-488c-b1be-a87f11bd5fa2/' +
            'statustypen/70ae2e9d-73a2-4f3d-849e-e0a29ef3064e'
        )
        enkelvoudiginformatieobject_url = (
            'https://ref.tst.vng.cloud/drc/api/v1/enkelvoudiginformatieobjecten/' +
            '1239d6b1-194a-4052-85c5-8c2876428531'
        )

        signal = SignalFactory()
        case_signal = CaseSignalFactory(signal=signal)
        serializer = SignalZDSSerializer(signal)

        self.get_mock(mock, 'zrc_openapi')
        self.get_mock(mock, 'zrc_zaak_read', url=case_signal.zrc_link)
        self.get_exception_mock(mock, 'zrc_status_list', ClientError)
        self.get_mock(mock, 'ztc_openapi')
        self.get_mock(mock, 'ztc_statustypen_read', url=status_type_url)
        self.get_mock(mock, 'drc_openapi')
        self.get_mock(mock, 'drc_objectinformatieobject_list')
        self.get_mock(mock, 'drc_objectinformatieobject_list', url=enkelvoudiginformatieobject_url)

        self.assertEqual(serializer.data, {
            'id': signal.id,
            'zds_case': {
                'url': 'http://example.com',
                'identificatie': 'string',
                'bronorganisatie': 'string',
                'omschrijving': 'string',
                'zaaktype': 'http://example.com',
                'registratiedatum': '2018-11-14',
                'verantwoordelijkeOrganisatie': 'http://example.com',
                'startdatum': '2018-11-14',
                'einddatum': '2018-11-14',
                'einddatumGepland': '2018-11-14',
                'uiterlijkeEinddatumAfdoening': '2018-11-14',
                'toelichting': 'string',
                'zaakgeometrie': {
                    'type': 'Point',
                    'coordinates': [0, 0]
                },
                'status': 'http://example.com',
                'kenmerken': [{
                    'kenmerk': 'string',
                    'bron': 'string'
                }]
            },
            'zds_statusses': [],
            'zds_images': [{
                'url': 'http://example.com',
                'informatieobject': [{
                    'url': 'http://example.com',
                    'informatieobject': 'https://ref.tst.vng.cloud/drc/api/v1/enkelvoudiginformatieobjecten/1239d6b1-194a-4052-85c5-8c2876428531',
                    'object': 'http://example.com',
                    'objectType': 'besluit',
                    'aardRelatieWeergave': 'Hoort bij, omgekeerd: kent',
                    'titel': 'string',
                    'beschrijving': 'string',
                    'registratiedatum': '2018-11-20T10:32:25Z'
                }],
                'object': 'http://example.com',
                'objectType': 'besluit',
                'aardRelatieWeergave': 'Hoort bij, omgekeerd: kent',
                'titel': 'string',
                'beschrijving': 'string',
                'registratiedatum': '2018-11-20T10:32:25Z'
            }]
        })

    @requests_mock.Mocker()
    def test_with_signal_case_image_error(self, mock):
        status_type_url = (
            'https://ref.tst.vng.cloud/ztc/api/v1/catalogussen/' +
            '8ffb11f0-c7cc-4e35-8a64-a0639aeb8f18/zaaktypen/c2f952ca-298e-488c-b1be-a87f11bd5fa2/' +
            'statustypen/70ae2e9d-73a2-4f3d-849e-e0a29ef3064e'
        )
        enkelvoudiginformatieobject_url = (
            'https://ref.tst.vng.cloud/drc/api/v1/enkelvoudiginformatieobjecten/' +
            '1239d6b1-194a-4052-85c5-8c2876428531'
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
        self.get_exception_mock(mock, 'drc_objectinformatieobject_list', ClientError)

        self.assertEqual(serializer.data, {
            'id': signal.id,
            'zds_case': {
                'url': 'http://example.com',
                'identificatie': 'string',
                'bronorganisatie': 'string',
                'omschrijving': 'string',
                'zaaktype': 'http://example.com',
                'registratiedatum': '2018-11-14',
                'verantwoordelijkeOrganisatie': 'http://example.com',
                'startdatum': '2018-11-14',
                'einddatum': '2018-11-14',
                'einddatumGepland': '2018-11-14',
                'uiterlijkeEinddatumAfdoening': '2018-11-14',
                'toelichting': 'string',
                'zaakgeometrie': {
                    'type': 'Point',
                    'coordinates': [0, 0]
                },
                'status': 'http://example.com',
                'kenmerken': [{
                    'kenmerk': 'string',
                    'bron': 'string'
                }]
            },
            'zds_statusses': [{
                'url': 'http://example.com',
                'zaak': 'http://example.com',
                'statusType': {
                    'url': 'http://example.com',
                    'omschrijving': 'Gemeld',
                    'omschrijvingGeneriek': 'string',
                    'statustekst': 'string',
                    'isVan': 'http://example.com',
                    'volgnummer': 1,
                    'isEindstatus': True
                },
                'datumStatusGezet': '2018-11-20T10:34:43Z',
                'statustoelichting': 'string'
            }],
            'zds_images': []
        })
