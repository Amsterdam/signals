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
from signals.apps.zds.workflow import ZTC_STATUSSES

from .models import ZaakSignal

logger = logging.getLogger(__name__)


def create_case(signal):
    """
    This will create a case in the ZRC.
    """
    # If the signal already has a case connected.
    # It is not needed to create a case.
    try:
        signal.zaak
        return
    except ObjectDoesNotExist:
        pass

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
            "coordinates": list(signal.location.point.coords),
        },
    }

    if signal.expire_date:
        data['uiterlijkeEinddatumAfdoening'] = signal.expire_date.strftime('%Y-%m-%d')

    try:
        response = zds_client.zrc.create('zaak', data)
        ZaakSignal.actions.create_zaak_signal(response.get('url'), signal)
    except (ClientError, ConnectionError) as error:
        logger.exception(error)
        raise CaseNotCreatedException()


def connect_signal_to_case(signal):
    """
    This will create a connection between the case and the signal.
    Now from the ZRC you wull know which signal has more detailed information.
    """
    data = {
        'zaak': signal.zaak.zrc_link,
        'object': settings.HOST_URL + reverse('v0:signal-auth-detail', kwargs={'pk': signal.id}),
        'type': settings.ZRC_ZAAKOBJECT_TYPE
    }

    try:
        zds_client.zrc.create('zaakobject', data)
    except (ClientError, ConnectionError) as error:
        logger.exception(error)
        raise CaseConnectionException()


def add_status_to_case(signal):
    """
    This will create a new status for an existing case. If the case already has a status.
    A new status will be created. Always the latest created status will be the active one.
    """
    data = {
        'zaak': signal.zaak.zrc_link,
        'statusType': ZTC_STATUSSES.get(signal.status.state),
        'datumStatusGezet': signal.status.created_at.isoformat(),
    }

    if signal.status.text:
        data['statustoelichting'] = signal.status.text

    try:
        zds_client.zrc.create('status', data)
    except (ClientError, ConnectionError) as error:
        logger.exception(error)
        raise StatusNotCreatedException()


def create_document(signal):
    """
    This will create a document in the DRC. This will be base of the photo upload.
    """
    with open(signal.image.path, 'br') as tmp_file:
        image_data = tmp_file.read()

    data = {
        'creatiedatum': timezone.now().strftime('%Y-%m-%d'),
        'titel': signal.image.name,
        'auteur': 'SIA Amsterdam',
        'taal': 'dut',
        'informatieobjecttype': settings.ZTC_INFORMATIEOBJECTTYPE_URL,
        'inhoud': base64.b64encode(image_data),
    }

    try:
        response = zds_client.drc.create("enkelvoudiginformatieobject", data)
        ZaakSignal.actions.add_document(response.get('url'), signal.zaak)
    except (ClientError, ConnectionError) as error:
        logger.exception(error)
        raise DocumentNotCreatedException()


def add_document_to_case(signal):
    """
    This will connect the document to the case.
    """
    data = {
        'informatieobject': signal.zaak.document_url,
        'object': signal.zaak.zrc_link,
        'objectType': 'zaak',
        'registratiedatum': timezone.now().isoformat(),
    }

    try:
        zds_client.drc.create('objectinformatieobject', data)
    except (ClientError, ConnectionError) as error:
        logger.exception(error)
        raise DocumentConnectionException()


#
# Iteration 2
#
# def get_case(signal):
#     """
#     This will get the case with all needed data.

#     :return: response
#     """
#     response = zds_client.zrc.retrieve('zaak', url=signal.zaak.zrc_link)
#     return response


# def get_documents_from_case(signal):
#     """
#     This will fetch all documents connected to the case

#     :return: response
#     """
#     raise NotImplementedError()


# def get_status_history(signal):
#     """
#     This will fetch all statusses that are connected to the

#     :return: response
#     """
#     raise NotImplementedError()


#
# Iteration 3
#
# def get_all_statusses():
#     """
#     This will fetch all statusses that exists in the ZTC.

#     :return: response
#     """
#     path_kwargs = {
#         'catalogus_uuid': settings.ZTC_CATALOGUS,
#         'zaaktype_uuid': settings.ZTC_ZAAKTYPE
#     }

#     response = zds_client.ztc.list('statustype', **path_kwargs)
#     return response
