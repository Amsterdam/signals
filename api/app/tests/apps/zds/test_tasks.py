import requests_mock
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase, override_settings
from django.utils import timezone

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
    create_document,
    get_all_statusses,
    get_case,
    get_documents_from_case,
    get_information_object,
    get_status,
    get_status_history,
    get_status_type
)
from tests.apps.signals.factories import SignalFactory, SignalFactoryWithImage
from tests.apps.zds.factories import CaseDocumentFactory, CaseSignalFactory, CaseStatusFactory
from tests.apps.zds.mixins import ZDSMockMixin


class TestTasks(ZDSMockMixin, TestCase):
    @requests_mock.Mocker()
    def test_get_all_statusses(self, mock):
        self.get_mock(mock, 'ztc_openapi')
        self.get_mock(mock, 'ztc_statustypen_list')

        statusses = get_all_statusses()
        self.assertEqual(statusses, [
            {
                "url": "http://example.com",
                "omschrijving": "Gemeld",
                "omschrijvingGeneriek": "string",
                "statustekst": "string",
                "isVan": "http://example.com",
                "volgnummer": 1,
                "isEindstatus": True
            },
            {
                "url": "http://example.com",
                "omschrijving": "Done",
                "omschrijvingGeneriek": "string",
                "statustekst": "string",
                "isVan": "http://example.com",
                "volgnummer": 1,
                "isEindstatus": True
            }
        ])

    @requests_mock.Mocker()
    def test_get_status(self, mock):
        self.get_mock(mock, 'ztc_openapi')
        self.get_mock(mock, 'ztc_statustypen_list')

        status = get_status('Gemeld')
        self.assertEqual(status, {
            'isEindstatus': True,
            'isVan': 'http://example.com',
            'omschrijving': 'Gemeld',
            'omschrijvingGeneriek': 'string',
            'statustekst': 'string',
            'url': 'http://example.com',
            'volgnummer': 1
        })

    @requests_mock.Mocker()
    def test_get_status_no_match(self, mock):
        self.get_mock(mock, 'ztc_openapi')
        self.get_mock(mock, 'ztc_statustypen_list')

        status = get_status('Not_matching_any_status')
        self.assertEqual(status, {})

    @requests_mock.Mocker()
    def test_create_case_no_case(self, mock):
        self.get_mock(mock, 'zrc_openapi')
        self.post_mock(mock, 'zrc_zaak_create')

        signal = SignalFactory()
        create_case(signal)
        self.assertTrue(hasattr(signal, 'case'))

    @requests_mock.Mocker()
    def test_create_case_with_expire_date(self, mock):
        self.get_mock(mock, 'zrc_openapi')
        self.post_mock(mock, 'zrc_zaak_create')

        signal = SignalFactory(expire_date=timezone.now())
        create_case(signal)
        self.assertTrue(hasattr(signal, 'case'))

    @requests_mock.Mocker()
    def test_create_case_with_case(self, mock):
        case_signal = CaseSignalFactory()
        create_case(case_signal.signal)

    @requests_mock.Mocker()
    def test_create_case_with_case_no_zrc_link(self, mock):
        self.get_mock(mock, 'zrc_openapi')
        self.post_mock(mock, 'zrc_zaak_create')

        case_signal = CaseSignalFactory(zrc_link=None)
        create_case(case_signal.signal)

    @requests_mock.Mocker()
    def test_create_case_with_error(self, mock):
        self.get_mock(mock, 'zrc_openapi')
        self.post_error_mock(mock, 'zrc_zaak_create')

        signal = SignalFactory()

        with self.assertRaises(CaseNotCreatedException):
            create_case(signal)

    @requests_mock.Mocker()
    def test_connect_signal_to_case(self, mock):
        self.get_mock(mock, 'zrc_openapi')
        self.post_mock(mock, 'zrc_zaak_create')
        self.post_mock(mock, 'zrc_zaakobject_create')

        signal = SignalFactory()
        create_case(signal)
        connect_signal_to_case(signal)

    @requests_mock.Mocker()
    def test_connect_signal_to_case_already_done(self, mock):
        self.get_mock(mock, 'zrc_openapi')
        self.post_error_mock(mock, 'zrc_zaakobject_create')

        case_signal = CaseSignalFactory(connected_in_external_system=True)

        connect_signal_to_case(case_signal.signal)

    @override_settings(ZRC_ZAAKOBJECT_TYPE='random')
    @requests_mock.Mocker()
    def test_connect_signal_to_case_error(self, mock):
        self.get_mock(mock, 'zrc_openapi')
        self.post_error_mock(mock, 'zrc_zaakobject_create')

        case_signal = CaseSignalFactory()

        with self.assertRaises(CaseConnectionException):
            connect_signal_to_case(case_signal.signal)

    @requests_mock.Mocker()
    def test_add_status_to_case(self, mock):
        self.get_mock(mock, 'zrc_openapi')
        self.get_mock(mock, 'ztc_openapi')
        self.get_mock(mock, 'ztc_statustypen_list')
        self.post_mock(mock, 'zrc_status_create')

        case_signal = CaseSignalFactory()
        add_status_to_case(case_signal.signal, case_signal.signal.status)

    @requests_mock.Mocker()
    def test_add_status_to_case_status_already_exists(self, mock):
        self.get_mock(mock, 'zrc_openapi')
        self.get_mock(mock, 'ztc_openapi')
        self.get_mock(mock, 'ztc_statustypen_list')
        self.post_mock(mock, 'zrc_status_create')

        case_signal = CaseSignalFactory()
        CaseStatusFactory(case_signal=case_signal)
        add_status_to_case(case_signal.signal, case_signal.signal.status)

    @requests_mock.Mocker()
    def test_add_status_to_case_no_zrc_link(self, mock):
        self.get_mock(mock, 'zrc_openapi')
        self.get_mock(mock, 'ztc_openapi')
        self.get_mock(mock, 'ztc_statustypen_list')
        self.post_mock(mock, 'zrc_status_create')

        case_signal = CaseSignalFactory()
        CaseStatusFactory(case_signal=case_signal, zrc_link='', status=case_signal.signal.status)
        add_status_to_case(case_signal.signal, case_signal.signal.status)

    @requests_mock.Mocker()
    def test_add_status_to_case_with_no_text(self, mock):
        self.get_mock(mock, 'zrc_openapi')
        self.get_mock(mock, 'ztc_openapi')
        self.get_mock(mock, 'ztc_statustypen_list')
        self.post_mock(mock, 'zrc_status_create')

        case_signal = CaseSignalFactory(signal__status__text='')
        add_status_to_case(case_signal.signal, case_signal.signal.status)

    @requests_mock.Mocker()
    def test_add_status_to_case_with_error(self, mock):
        self.get_mock(mock, 'zrc_openapi')
        self.get_mock(mock, 'ztc_openapi')
        self.get_mock(mock, 'ztc_statustypen_list')
        self.post_error_mock(mock, 'zrc_status_create')

        case_signal = CaseSignalFactory()

        with self.assertRaises(StatusNotCreatedException):
            add_status_to_case(case_signal.signal, case_signal.signal.status)

    @requests_mock.Mocker()
    def test_create_document(self, mock):
        self.get_mock(mock, 'drc_openapi')
        self.post_mock(mock, 'drc_enkelvoudiginformatieobject_create')

        signal = SignalFactoryWithImage()
        CaseSignalFactory(signal=signal)
        create_document(signal)

    @requests_mock.Mocker()
    def test_create_document_already_exists(self, mock):
        self.get_mock(mock, 'drc_openapi')
        self.post_mock(mock, 'drc_enkelvoudiginformatieobject_create')

        signal = SignalFactoryWithImage()
        case_signal = CaseSignalFactory(signal=signal)
        CaseDocumentFactory(case_signal=case_signal)
        create_document(signal)

    @requests_mock.Mocker()
    def test_create_document_with_error(self, mock):
        signal = SignalFactory()

        with self.assertRaises(ObjectDoesNotExist):
            create_document(signal)

    @requests_mock.Mocker()
    def test_create_document_not_created_exception(self, mock):
        self.get_mock(mock, 'drc_openapi')
        self.post_error_mock(mock, 'drc_enkelvoudiginformatieobject_create')

        signal = SignalFactoryWithImage()
        CaseSignalFactory(signal=signal)

        with self.assertRaises(DocumentNotCreatedException):
            create_document(signal)

    @requests_mock.Mocker()
    def test_add_document_to_case(self, mock):
        self.get_mock(mock, 'drc_openapi')
        self.post_mock(mock, 'drc_enkelvoudiginformatieobject_create')
        self.post_mock(mock, 'drc_objectinformatieobject_create')

        signal = SignalFactoryWithImage()
        CaseSignalFactory(signal=signal)
        case_document = create_document(signal)
        add_document_to_case(signal, case_document)

    @requests_mock.Mocker()
    def test_add_document_to_case_already_connected(self, mock):
        self.get_mock(mock, 'drc_openapi')
        self.post_mock(mock, 'drc_enkelvoudiginformatieobject_create')
        self.post_mock(mock, 'drc_objectinformatieobject_create')

        signal = SignalFactoryWithImage()
        CaseSignalFactory(signal=signal)
        case_document = create_document(signal)
        case_document.connected_in_external_system = True
        add_document_to_case(signal, case_document)

    @requests_mock.Mocker()
    def test_add_document_to_case_with_error(self, mock):
        self.get_mock(mock, 'drc_openapi')
        self.post_mock(mock, 'drc_enkelvoudiginformatieobject_create')
        self.post_error_mock(mock, 'drc_objectinformatieobject_create')

        signal = SignalFactoryWithImage()
        CaseSignalFactory(signal=signal)
        case_document = create_document(signal)

        with self.assertRaises(DocumentConnectionException):
            add_document_to_case(signal, case_document)

    @requests_mock.Mocker()
    def test_get_case(self, mock):
        zaak_signal = CaseSignalFactory()
        self.get_mock(mock, 'zrc_openapi')
        self.get_mock(mock, 'zrc_zaak_read', url=zaak_signal.zrc_link)

        response = get_case(zaak_signal.signal)
        self.assertEqual(response, {
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
        })

    @requests_mock.Mocker()
    def test_get_case_no_case_connected(self, mock):
        signal = SignalFactory()

        response = get_case(signal)
        self.assertEqual(response, {})

    @requests_mock.Mocker()
    def test_get_documents_from_case(self, mock):
        zaak_signal = CaseSignalFactory()
        self.get_mock(mock, 'drc_openapi')
        self.get_mock(mock, 'drc_objectinformatieobject_list')

        response = get_documents_from_case(zaak_signal.signal)
        self.assertEqual(response, [
            {
                "url": "http://example.com",
                "informatieobject": (
                    "https://ref.tst.vng.cloud/drc/api/v1/enkelvoudiginformatieobjecten/" +
                    "1239d6b1-194a-4052-85c5-8c2876428531"
                ),
                "object": "http://example.com",
                "objectType": "besluit",
                "aardRelatieWeergave": "Hoort bij, omgekeerd: kent",
                "titel": "string",
                "beschrijving": "string",
                "registratiedatum": "2018-11-20T10:32:25Z"
            }
        ])

    @requests_mock.Mocker()
    def test_get_status_history(self, mock):
        zaak_signal = CaseSignalFactory()
        self.get_mock(mock, 'zrc_openapi')
        self.get_mock(mock, 'zrc_status_list')

        response = get_status_history(zaak_signal.signal)
        self.assertEqual(response, [
            {
                "url": "http://example.com",
                "zaak": "http://example.com",
                "statusType": (
                    "https://ref.tst.vng.cloud/ztc/api/v1/catalogussen/" +
                    "8ffb11f0-c7cc-4e35-8a64-a0639aeb8f18/zaaktypen/" +
                    "c2f952ca-298e-488c-b1be-a87f11bd5fa2/statustypen/" +
                    "70ae2e9d-73a2-4f3d-849e-e0a29ef3064e"
                ),
                "datumStatusGezet": "2018-11-20T10:34:43Z",
                "statustoelichting": "string"
            }
        ])

    @requests_mock.Mocker()
    def test_get_status_history_no_zrc_link(self, mock):
        zaak_signal = CaseSignalFactory(zrc_link='')
        self.get_mock(mock, 'zrc_openapi')
        self.get_mock(mock, 'zrc_status_list')

        response = get_status_history(zaak_signal.signal)
        self.assertEqual(response, [])

    @requests_mock.Mocker()
    def test_get_status_history_no_case(self, mock):
        signal = SignalFactory()

        response = get_status_history(signal)
        self.assertEqual(response, [])

    @requests_mock.Mocker()
    def test_get_status_type(self, mock):
        url = (
            'https://ref.tst.vng.cloud/ztc/api/v1/catalogussen/' +
            '8ffb11f0-c7cc-4e35-8a64-a0639aeb8f18/zaaktypen/c2f952ca-298e-488c-b1be-a87f11bd5fa2/' +
            'statustypen/70ae2e9d-73a2-4f3d-849e-e0a29ef3064e'
        )

        self.get_mock(mock, 'zrc_openapi')
        self.get_mock(mock, 'zrc_status_list')
        self.get_mock(mock, 'ztc_openapi')
        self.get_mock(mock, 'ztc_statustypen_read', url=url)

        case_status = CaseStatusFactory()

        statusses = get_status_history(case_status.case_signal.signal)
        response = get_status_type(statusses[0].get('statusType'))
        self.assertIsNotNone(response)

    @requests_mock.Mocker()
    def test_get_infromatie_object(self, mock):
        case_document = CaseDocumentFactory()

        oio_url = (
            'https://ref.tst.vng.cloud:443/drc/api/v1/objectinformatieobjecten?object={}'.format(
                case_document.case_signal.zrc_link)
        )
        eio_url = (
            'https://ref.tst.vng.cloud/drc/api/v1/enkelvoudiginformatieobjecten/' +
            '1239d6b1-194a-4052-85c5-8c2876428531'
        )

        self.get_mock(mock, 'zrc_openapi')
        self.get_mock(mock, 'drc_openapi')
        self.get_mock(mock, 'drc_objectinformatieobject_list', url=oio_url)
        self.get_mock(mock, 'drc_enkelvoudiginformatieobject_read', url=eio_url)

        documents = get_documents_from_case(case_document.case_signal.signal)
        response = get_information_object(documents[0].get('informatieobject'))
        self.assertIsNotNone(response)
