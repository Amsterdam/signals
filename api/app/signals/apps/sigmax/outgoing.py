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

SIGMAX_REQUIRED_ADDRESS_FIELDS = ['woonplaats', 'openbare_ruimte', 'huisnummer']


class SigmaxException(Exception):
    pass


# TODO SIG-593: implement data mapping if and when it is defined

def _generate_omschrijving(signal):
    """Generate brief descriptive text for list view in CityControl"""
    # Note: we do not mention main or subcategory here (too many characters)
    is_urgent = 'JA' if signal.priority.priority == Priority.PRIORITY_HIGH else 'NEE'
    stadsdeel = signal.location.stadsdeel or '-'

    return 'SIA-{} {} {} {}'.format(
        signal.id,
        is_urgent,
        stadsdeel,
        signal.location.short_address_text,
    )


def _address_matches_sigmax_expectation(address_dict):
    """Return whether an address has all information Sigmax/CityControl needs.

    Note: we do not validate the address against the Basisadministratie
    Adresses en Gebouwen (BAG). We do check that all required components are
    non-empty.
    """
    # TODO: consider checking the existence of an address / make it impossible
    # for non (BAG) validated addresses to reach Sigmax.
    # TODO: consider moving to a JSONSchema style check here (more concise)
    if not address_dict:  # protect against empty address fields
        return False

    for field in SIGMAX_REQUIRED_ADDRESS_FIELDS:
        if field not in address_dict:
            return False

    # We want a "huisnummer" to be (convertable to) an actual number
    try:
        int(address_dict['huisnummer'])
    except (ValueError, TypeError):
        return False

    # We want non-empty strings for "woonplaats" and "openbare_ruimte"
    if (not isinstance(address_dict['woonplaats'], str) or
            not isinstance(address_dict['openbare_ruimte'], str)):
        return False

    if (not address_dict['woonplaats'].strip() or
            not address_dict['openbare_ruimte'].strip()):
        return False

    return True


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
        'address_matches_sigmax_expectation':
            _address_matches_sigmax_expectation(signal.location.address),
        'signal': signal,
        'incident_date_end': signal.incident_date_end or incident_date_end,
        'x': str(signal.location.geometrie.x),
        'y': str(signal.location.geometrie.y),
        'omschrijving': _generate_omschrijving(signal),
    })


def _generate_voegZaakdocumentToe_Lk01(signal):
    """
    Generate XML for Sigmax voegZaakdocumentToe_Lk01 (for the PDF case)
    """
    # TODO: generalize, so that either PDF or JPG can be sent.
    encoded_pdf = _generate_pdf(signal)

    return render_to_string('sigmax/voegZaakdocumentToe_Lk01.xml', context={
        'signal': signal,
        'DOC_UUID': escape(str(uuid.uuid4())),
        'DATA': encoded_pdf.decode('utf-8'),
        'DOC_TYPE': 'PDF',
        'FILE_NAME': f'{signal.sia_id}.pdf'
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
        'Content-Length': b'%d' % len(encoded)
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
