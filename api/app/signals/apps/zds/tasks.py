import base64
import logging

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.utils import timezone
from requests.exceptions import ConnectionError
from zds_client import ClientError

from signals.apps.zds import zds_client
from signals.apps.zds.exceptions import (
    CaseConnectionException,
    CaseNotCreatedException,
    DocumentConnectionException,
    DocumentNotCreatedException,
    StatusNotCreatedException
)

from .models import CaseSignal

logger = logging.getLogger(__name__)


def get_all_statusses():
    """
    This will fetch all statusses that exists in the ZTC.

    :return: response
    """
    path_kwargs = {
        'catalogus_uuid': settings.ZTC_CATALOGUS_ID,
        'zaaktype_uuid': settings.ZTC_ZAAKTYPE_ID
    }

    response = zds_client.ztc.list(resource='statustype', **path_kwargs)
    return response


def get_status(status_name):
    """
    This will now be a local filter. This should ideally be done via the api.
    """
    statusses = get_all_statusses()
    for status in statusses:
        if status.get('omschrijving', '') == status_name:
            return status
    return {}


def create_case(signal):
    """
    This will create a case in the ZRC.
    """
    # If the signal already has a case connected.
    # It is not needed to create a case.
    try:
        case_signal = signal.case
        if case_signal.zrc_link:
            return case_signal
    except ObjectDoesNotExist:
        case_signal = CaseSignal.actions.create_case_signal(signal)

    data = {
        'bronorganisatie': settings.RSIN_NUMBER,
        'zaaktype': settings.ZTC_ZAAKTYPE_URL,
        'verantwoordelijkeOrganisatie': settings.RSIN_NUMBER,
        'startdatum': signal.incident_date_start.strftime('%Y-%m-%d'),
        'identificatie': str(signal.signal_id),
        'registratie_datum': signal.created_at.strftime('%Y-%m-%d'),
        # This is a hard limit in the ZRC.
        # It will give back an error if it is more that a 1000 characters
        'toelichting': signal.text[:1000],
        'zaakgeometrie': {
            "type": "Point",
            "coordinates": list(signal.location.geometrie.coords),
        }
    }

    if signal.expire_date:
        data['uiterlijkeEinddatumAfdoening'] = signal.expire_date.strftime('%Y-%m-%d')

    try:
        response = zds_client.zrc.create(resource='zaak', data=data)
        CaseSignal.actions.add_zrc_link(response.get('url'), case_signal)
        return case_signal
    except (ClientError, ConnectionError) as error:
        logger.exception(error)
        raise CaseNotCreatedException()


def connect_signal_to_case(signal):
    """
    This will create a connection between the case and the signal.
    Now from the ZRC you wull know which signal has more detailed information.
    """
    if signal.case.connected_in_external_system:
        return signal.case

    data = {
        'zaak': signal.case.zrc_link,
        'object': settings.HOST_URL + reverse('v0:signal-auth-detail', kwargs={'pk': signal.id}),
        'type': settings.ZRC_ZAAKOBJECT_TYPE
    }

    try:
        zds_client.zrc.create(resource='zaakobject', data=data)
        CaseSignal.actions.connected_in_external_system(signal.case)
        return signal.case
    except (ClientError, ConnectionError) as error:
        logger.exception(error)
        raise CaseConnectionException()


def add_status_to_case(signal, status):
    """
    This will create a new status for an existing case. If the case already has a status.
    A new status will be created. Always the latest created status will be the active one.
    """
    try:
        case_status = status.case_status
        if case_status.zrc_link:
            return case_status
    except ObjectDoesNotExist:

        case_status = CaseSignal.actions.add_status(signal.case, status)

    data = {
        'zaak': signal.case.zrc_link,
        'statusType': get_status(status.get_state_display()).get('url'),
        'datumStatusGezet': status.created_at.isoformat(),
    }

    if status.text:
        data['statustoelichting'] = status.text

    try:
        response = zds_client.zrc.create(resource='status', data=data)
        CaseSignal.actions.add_zrc_link(response.get('url'), case_status)
        return case_status
    except (ClientError, ConnectionError) as error:
        logger.exception(error)
        raise StatusNotCreatedException()


def create_document(signal):
    """
    This will create a document in the DRC. This will be base of the photo upload.
    """
    if (
        signal.case.documents.count() == 1 and
        signal.case.documents.order_by('created_at').first().drc_link is not None
    ):
        return signal.case.documents.first()

    case_document = CaseSignal.actions.add_document(signal.case)

    with open(signal.image.path, 'br') as tmp_file:
        image_data = tmp_file.read()

    data = {
        'bronorganisatie': settings.RSIN_NUMBER,
        'creatiedatum': timezone.now().strftime('%Y-%m-%d'),
        'titel': signal.image.name,
        'auteur': 'SIA Amsterdam',
        'taal': 'dut',
        'informatieobjecttype': settings.ZTC_INFORMATIEOBJECTTYPE_URL,
        'inhoud': base64.b64encode(image_data),
    }

    try:
        response = zds_client.drc.create(resource="enkelvoudiginformatieobject", data=data)
        CaseSignal.actions.add_drc_link(response.get('url'), case_document)
        return case_document
    except (ClientError, ConnectionError) as error:
        logger.exception(error)
        raise DocumentNotCreatedException()


def add_document_to_case(signal, case_document):
    """
    This will connect the document to the case.
    """
    if case_document.connected_in_external_system:
        return case_document

    data = {
        'informatieobject': signal.case.document_url,
        'object': signal.case.zrc_link,
        'objectType': 'zaak',
        'registratiedatum': timezone.now().isoformat(),
    }

    try:
        zds_client.drc.create(resource='objectinformatieobject', data=data)
        CaseSignal.actions.connected_in_external_system(case_document)
        return case_document
    except (ClientError, ConnectionError) as error:
        logger.exception(error)
        raise DocumentConnectionException()


def get_case(signal):
    """
    This will get the case with all needed data.

    :return: response
    """
    if hasattr(signal, 'case') and signal.case.zrc_link:
        response = zds_client.zrc.retrieve(resource='zaak', url=signal.case.zrc_link)
        return response
    return {}


def get_documents_from_case(signal):
    """
    This will fetch all documents connected to the case

    :return: response
    """
    response = zds_client.drc.list(resource='objectinformatieobject', query_params={
        'object': signal.case.zrc_link})
    return response


def get_status_history(signal):
    """
    This will fetch all statusses that are connected to the

    :return: response
    """
    try:
        if not signal.case.zrc_link:
            return []
        response = zds_client.zrc.list(resource='status', query_params={
            'zaak': signal.case.zrc_link})
        return response
    except ObjectDoesNotExist:
        return []


def get_status_type(url):
    """
    This will fetch the needed information to show what type of status is fetched.
    """
    response = zds_client.ztc.retrieve(resource='statustype', url=url)
    return response


def get_information_object(url):
    """
    This is used to be able to get the content url for the needed document.
    """
    response = zds_client.drc.retrieve(resource='enkelvoudiginformatieobject', url=url)
    return response
