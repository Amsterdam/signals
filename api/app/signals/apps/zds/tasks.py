import logging

from django.conf import settings
from django.utils import timezone

from signals.apps.signals.models import Signal
from signals.apps.signals.workflow import ZTC_STATUSSES
from signals.apps.zds import zds_client

logger = logging.getLogger(__name__)


#
# Iteration 1
#
def create_case(signal):
    """
    This will create a case in the ZRC.

    :return: Signal object
    """
    data = {
        'bronorganisatie': 120177080,  # Deze moet opgevraagd worden wat dit zou moeten zijn voor de gemeente amsterdam
        'zaaktype': settings.ZTC_ZAAKTYPE_URL,
        'verantwoordelijkeOrganisatie': 'http://maykinmedia.nl/',  # nog geen idee waar deze vandaar komt. Lijk mij het ZTC te zijn...
        'startdatum': signal.incident_date_start.strftime('%Y-%m-%d'),
    }

    try:
        response = zds_client.zrc.create('zaak', data)
        signal = Signal.actions.add_case(response, signal)
    except Exception as exception:
        logger.exception(exception)

    return signal


def connect_signal_to_case(signal):
    """
    This will create a connection between the case and the signal. Now from the ZRC you wull know
    which signal has more detailed information.

    :return: Signal object
    """
    data = {
        'zaak': signal.zaak_url,
        'object': signal.get_absolute_url(),
        'type': settings.ZRC_ZAAKOBJECT_TYPE
    }
    response = zds_client.zrc.create('zaakobject', data)
    # TODO: Handle error cases.
    return signal


def add_status_to_case(signal):
    """
    This will create a new status for an existing case. If the case already has a status.
    A new status will be created. Always the latest created status will be the active one.

    :return: Signal object
    """
    data = {
        'zaak': signal.zaak_url,
        'statusType': ZTC_STATUSSES.get(signal.status.state),
        'datumStatusGezet': signal.status.created_at.isoformat(),
    }

    response = zds_client.zrc.create('status', data)
    # TODO: Handle error cases.
    return signal


def create_document(signal):
    """
    This will create a document in the DRC. This will be base of the photo upload.

    :return: Signal object
    """
    data = {
        'creatiedatum': timezone.now().strftime('%Y-%m-%d'),
        'titel': signal.image.file,
        'auteur': 'SIA Amsterdam',
        'taal': 'dut',
        'informatieobjecttype': settings.ZTC_INFORMATIEOBJECTTYPE_URL,
        'inhoud': signal.image.file.read(),
    }

    try:
        response = zds_client.drc.create("enkelvoudiginformatieobject", data)
        signal = Signal.actions.add_document(response)
    except Exception as exception:
        logger.exception(exception)

    return signal


def add_document_to_case(signal):
    """
    This will connect the document to the case.

    :return: Signal object
    """
    data = {
        'informatieobject': signal.document_url,
        'object': signal.zaak_url,
        'objectType': 'zaak',
        'registratiedatum': timezone.now().isoformat(),
    }

    response = zds_client.drc.create('objectinformatieobject', data)
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
    response = zds_client.zrc.retrieve('zaak', url=signal.zaak_url)
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
