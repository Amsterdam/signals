"""
Handle sending a signal to sigmax.
Retry logic ao are handled by Celery.
"""
import logging
import uuid

from django.template.loader import render_to_string
from lxml import etree

from signals.apps.sigmax.stuf_protocol.outgoing.creeerZaak_Lk01 import (
    _generate_sequence_number,
    _send_stuf_message
)
from signals.apps.sigmax.stuf_protocol.outgoing.pdf import _generate_pdf

logger = logging.getLogger(__name__)


VOEG_ZAAKDOCUMENT_TOE_SOAPACTION = \
    '"http://www.egem.nl/StUF/sector/zkn/0310/VoegZaakdocumentToe_Lk01"'


def _generate_voegZaakdocumentToe_Lk01(signal):
    """
    Generate XML for Sigmax voegZaakdocumentToe_Lk01 (for the PDF case)
    """
    # TODO: generalize, so that either PDF or JPG can be sent.
    encoded_pdf = _generate_pdf(signal)
    sequence_number = _generate_sequence_number(signal)

    return render_to_string('sigmax/voegZaakdocumentToe_Lk01.xml', context={
        'signal': signal,
        'sequence_number': sequence_number,
        'DOC_UUID': str(uuid.uuid4()),
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


def send_voegZaakdocumentToe_Lk01(signal):
    # TODO: refactor message generation to support PDF and JPG
    #       arguments like: (signal, encoded_message, doctype)
    soap_action = VOEG_ZAAKDOCUMENT_TOE_SOAPACTION
    msg = _generate_voegZaakdocumentToe_Lk01(signal)
    response = _send_stuf_message(msg, soap_action)

    logger.info('Sent %s', soap_action)
    logger.info('Received:\n%s', response.text)
    return response
