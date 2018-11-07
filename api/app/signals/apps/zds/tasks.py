import base64
import logging

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.utils import timezone

from signals.apps.signals.workflow import ZTC_STATUSSES
from signals.apps.zds import zds_client
from signals.apps.zds.exceptions import CaseNotCreatedException, DocumentNotCreatedException

from .models import ZaakSignal

logger = logging.getLogger(__name__)


def create_case(signal):
    """
    This will create a case in the ZRC.

    :return: Signal object
    """
    # If the signal already has a case connected.
    # It is not needed to create a case.
    try:
        signal.zaak
        return signal
    except ObjectDoesNotExist:
        pass

    data = {
        # Deze moet opgevraagd worden wat dit zou moeten zijn voor de
        # gemeente amsterdam
        'bronorganisatie': 120177080,
        'zaaktype': settings.ZTC_ZAAKTYPE_URL,
        # nog geen idee waar deze vandaar komt. Lijk mij het ZTC te zijn...
        'verantwoordelijkeOrganisatie': 'http://maykinmedia.nl/',
        'startdatum': signal.incident_date_start.strftime('%Y-%m-%d'),
    }

    try:
        response = zds_client.zrc.create('zaak', data)
        ZaakSignal.actions.create_zaak_signal(response.get('url'), signal)
    except Exception as exception:
        logger.exception(exception)
        raise CaseNotCreatedException

    return signal


def connect_signal_to_case(signal):
    """
    This will create a connection between the case and the signal.
    Now from the ZRC you wull know which signal has more detailed information.

    :return: Signal object
    """
    data = {
        'zaak': signal.zaak.zrc_link,
        'object': settings.HOST_URL + reverse('v0:signal-auth-detail', kwargs={'pk': signal.id}),
        'type': settings.ZRC_ZAAKOBJECT_TYPE
    }
    zds_client.zrc.create('zaakobject', data)
    # TODO: Handle error cases.
    return signal


def add_status_to_case(signal):
    """
    This will create a new status for an existing case. If the case already has a status.
    A new status will be created. Always the latest created status will be the active one.

    :return: Signal object
    """
    data = {
        'zaak': signal.zaak.zrc_link,
        'statusType': ZTC_STATUSSES.get(signal.status.state),
        'datumStatusGezet': signal.status.created_at.isoformat(),
    }

    zds_client.zrc.create('status', data)
    # TODO: Handle error cases.
    return signal


def create_document(signal):
    """
    This will create a document in the DRC. This will be base of the photo upload.

    :return: Signal object
    """
    data = {
        'creatiedatum': timezone.now().strftime('%Y-%m-%d'),
        'titel': signal.image.name,
        'auteur': 'SIA Amsterdam',
        'taal': 'dut',
        'informatieobjecttype': settings.ZTC_INFORMATIEOBJECTTYPE_URL,
        'inhoud': base64.b64encode(signal.image.file.read()),
    }

    try:
        response = zds_client.drc.create("enkelvoudiginformatieobject", data)
        ZaakSignal.actions.add_document(response.get('url'), signal.zaak)
    except Exception as exception:
        logger.exception(exception)
        raise DocumentNotCreatedException()

    return signal


def add_document_to_case(signal):
    """
    This will connect the document to the case.

    :return: Signal object
    """
    data = {
        'informatieobject': signal.zaak.document_url,
        'object': signal.zaak.zrc_link,
        'objectType': 'zaak',
        'registratiedatum': timezone.now().isoformat(),
    }

    zds_client.drc.create('objectinformatieobject', data)
    # TODO: Handle error cases.
    return signal


#
# Iteration 2
#
def get_case(signal):
    """
    This will get the case with all needed data.

    :return: response
    """
    response = zds_client.zrc.retrieve('zaak', url=signal.zaak.zrc_link)
    return response


def get_documents_from_case(signal):
    """
    This will fetch all documents connected to the case

    :return: response
    """
    raise NotImplementedError()


def get_status_history(signal):
    """
    This will fetch all statusses that are connected to the

    :return: response
    """
    raise NotImplementedError()


#
# Iteration 3
#
def get_all_statusses():
    """
    This will fetch all statusses that exists in the ZTC.

    :return: response
    """
    path_kwargs = {
        'catalogus_uuid': settings.ZTC_CATALOGUS,
        'zaaktype_uuid': settings.ZTC_ZAAKTYPE
    }

    response = zds_client.ztc.list('statustype', **path_kwargs)
    return response
