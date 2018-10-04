"""
Handle sending a signal to sigmax.
Retry logic ao are handled by Celery.
"""
import logging
import os
import uuid
from datetime import timedelta
from xml.sax.saxutils import escape

import requests
from django.conf import settings
from django.template.loader import render_to_string
from lxml import etree

from signals.apps.sigmax.pdf import _generate_pdf
from signals.apps.signals.models import Priority, Signal

logger = logging.getLogger(__name__)

# The double quotes are part of the SOAP spec
CREEER_ZAAK_SOAPACTION = \
    '"http://www.egem.nl/StUF/sector/zkn/0310/CreeerZaak_Lk01"'

VOEG_ZAAKDOCUMENT_TOE_SOAPACTION = \
    '"http://www.egem.nl/StUF/sector/zkn/0310/VoegZaakdocumentToe_Lk01"'

SIGNALS_API_BASE = os.getenv('SIGNALS_API_BASE',
                             'https://acc.api.data.amsterdam.nl')


class SigmaxException(Exception):
    pass


# TODO SIG-593: implement data mapping if and when it is defined

def _generate_creeerZaak_Lk01(signal):
    """Generate XML for Sigmax creeerZaak_Lk01

    SIGMAX will be set up to receive Signals (meldingen) that have no address but do have
    coordinates (middle of park, somewhere on a body of water, etc.).
    """
    num_days_priority_mapping = {
        Priority.PRIORITY_HIGH: 1,
        Priority.PRIORITY_NORMAL: 3,
    }
    incident_date_end = (
        signal.created_at + timedelta(days=num_days_priority_mapping[signal.priority.priority]))

    return render_to_string('sigmax/creeerZaak_Lk01.xml', context={
        'signal': signal,
        'incident_date_end': signal.incident_date_end or incident_date_end,
    })


def _generate_voegZaakdocumentToe_Lk01(signal):
    """
    Generate XML for Sigmax voegZaakdocumentToe_Lk01 (for the PDF case)
    """
    # TODO: generalize, so that either PDF or JPG can be sent.
    encoded_pdf = _generate_pdf(signal)

    return render_to_string('sigmax/voegZaakdocumentToe_Lk01.xml', context={
        'ZKN_UUID': str(signal.signal_id),
        'DOC_UUID': escape(str(uuid.uuid4())),
        'DATA': encoded_pdf.decode('utf-8'),
        'DOC_TYPE': 'PDF',
        'FILE_NAME': f'MORA-{str(signal.id)}.pdf'
    })


def _stuf_response_ok(response):
    """
    Checks that a response is a Bv03 message.
    """
    namespaces = {
        'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
        'stuf': 'http://www.egem.nl/StUF/StUF0301',
    }

    try:
        tree = etree.fromstring(response.text)  # raises if not XML
    except etree.XMLSyntaxError:
        return False

    found = tree.xpath('//stuf:stuurgegevens/stuf:berichtcode', namespaces=namespaces)

    if len(found) != 1 or found[0].text != 'Bv03':
        return False
    return True


def _send_stuf_message(stuf_msg: str, soap_action: str):
    """
    Send a STUF message to the server that is configured.
    """
    if not settings.SIGMAX_AUTH_TOKEN or not settings.SIGMAX_SERVER:
        raise SigmaxException('SIGMAX_AUTH_TOKEN or SIGMAX_SERVER not configured.')

    # Prepare our request to Sigmax
    encoded = stuf_msg.encode('utf-8')

    headers = {
        'SOAPAction': soap_action,
        'Content-Type': 'text/xml; charset=UTF-8',
        'Authorization': 'Basic ' + settings.SIGMAX_AUTH_TOKEN,
        'Content-Length': bytes(len(encoded))
    }

    # Send our message to Sigmax. Network problems, and HTTP status codes
    # are all raised as errors.
    try:
        response = requests.post(
            url=settings.SIGMAX_SERVER,
            headers=headers,
            data=encoded,
            verify=False
        )
        response.raise_for_status()
    except requests.RequestException as e:
        raise SigmaxException from e

    # Inspect response content with lxml, check for Fo03/Bv03. Raise if we
    # receive anything other than XML or a message `berichtcode` other than
    # StUF Bv03.
    if not _stuf_response_ok(response):
        raise SigmaxException('Geen Bv03 ontvangen van Sigmax/CityControl')

    return response


def send_creeerZaak_Lk01(signal):
    soap_action = CREEER_ZAAK_SOAPACTION
    msg = _generate_creeerZaak_Lk01(signal)
    response = _send_stuf_message(msg, soap_action)

    logger.info('Sent %s', soap_action)
    logger.info('Received:\n%s', response.text)
    return response


def send_voegZaakdocumentToe_Lk01(signal):
    # TODO: refactor message generation to support PDF and JPG
    #       arguments like: (signal, encoded_message, doctype)
    soap_action = VOEG_ZAAKDOCUMENT_TOE_SOAPACTION
    msg = _generate_voegZaakdocumentToe_Lk01(signal)
    response = _send_stuf_message(msg, soap_action)

    logger.info('Sent %s', soap_action)
    logger.info('Received:\n%s', response.text)
    return response


def handle(signal: Signal) -> None:
    """
    Create a case (zaak) in Sigmax/CityControl, attach extra info in PDF
    """
    # Note: functions below may raise, exceptions are handled at Celery level.
    send_creeerZaak_Lk01(signal)
    send_voegZaakdocumentToe_Lk01(signal)
