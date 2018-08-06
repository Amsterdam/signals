"""
Handle sending a signal to sigmax.
Retry logic ao are handled by Celery.
"""
import base64
import logging
import os
import uuid
from xml.sax.saxutils import escape
from django.conf import settings

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from signals.models import Signal
from signals.integrations.sigmax.sigmax_pdf import _generate_pdf
from signals.integrations.sigmax.sigmax_xml_templates import CREER_ZAAK
from signals.integrations.sigmax.sigmax_xml_templates import VOEG_ZAAK_DOCUMENT_TOE

CREEER_ZAAK_SOAPACTION = \
    'http://www.egem.nl/StUF/sector/zkn/0310/CreeerZaak_Lk01'

VOEG_ZAAKDOCUMENT_TOE_SOAPACTION = \
    'http://www.egem.nl/StUF/sector/zkn/0310/VoegZaakdocumentToe_Lk01'

logger = logging.getLogger(__name__)

SIGNALS_API_BASE = os.getenv('SIGNALS_API_BASE',
                             'https://acc.api.data.amsterdam.nl')
PLACEHOLDER_STRING = ''


class ServiceNotConfigured(Exception):
    pass


def _format_datetime(dt):
    """Format datetime as YYYYMMDDHHMMSS."""
    return dt.strftime('%Y%m%d%H%M%S')


def _format_date(dt):
    """Format date as YYYYMMDD."""
    return dt.strftime('%Y%m%d')


def _get_session_with_retries():
    """
    There can be a some delays in processing from Sigmax. This retry logic
    handles most of that without having to reschedule the task. If this fails
    normal celery retry logic wil be applied.

    Get a requests Session that will retry 5 times
    on a number of HTTP 500 statusses.
    """
    session = requests.Session()

    retries = Retry(
        total=5,
        backoff_factor=0.1,
        status_forcelist=[500, 502, 503, 504],
        raise_on_status=True
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('https://', adapter)
    session.mount('http://', adapter)

    return session


def _generate_creeer_zaak_lk01_message(signal: Signal):
    """
    Generate XML for Sigmax CreeerZaak_Lk01
    """
    return CREER_ZAAK.format(**{
        'PRIMARY_KEY': str(signal.signal_id),
        'OMSCHRIJVING': escape(signal.text),
        'TIJDSTIPBERICHT': escape(_format_datetime(signal.created_at)),
        'STARTDATUM': escape(_format_date(signal.incident_date_start)),
        'REGISTRATIEDATUM': escape(_format_date(signal.created_at)),
        'EINDDATUMGEPLAND': escape(_format_date(signal.incident_date_end)),
        'OPENBARERUIMTENAAM': escape(signal.location.address['openbare_ruimte']),
        'HUISNUMMER': escape(signal.location.address['huisnummer']),
        'POSTCODE': escape(signal.location.address['postcode']),
        'X': escape(str(signal.location.geometrie['coordinates'][0])),
        'Y': escape(str(signal.location.geometrie['coordinates'][1])),
    })


def _generate_voeg_zaak_document_toe_lk01(signal: Signal):
    """
    Generate XML for Sigmax VoegZaakdocumentToe_Lk01 (for the PDF case)
    """
    encoded_pdf = _generate_pdf(signal)
    msg = VOEG_ZAAK_DOCUMENT_TOE.format(**{
        'ZKN_UUID': str(signal.signal_id),
        'DOC_UUID': escape(str(uuid.uuid4())),
        'DATA': encoded_pdf.decode('utf-8'),
        'DOC_TYPE': 'PDF',
        'DOC_TYPE_LOWER': 'pdf',
        'FILE_NAME': f'MORA-{str(signal.id)}.pdf'
    })

    return msg


def _generate_voeg_zaak_document_toe_lk01_jpg(signal: Signal):
    """
    Generate XML for Sigmax VoegZaakdocumentToe_Lk01 (for the JPG case)
    """
    encoded_jpg = b''
    if signal.image and signal.image.startswith('http'):
        # TODO: add check that we have a JPG and not anything else!
        try:
            result = requests.get(signal['image'])
        except:
            pass  # for now swallow 404, 401 etc
        else:
            encoded_jpg = result.content
    else:
        # TODO: CODE PATH FOR TESTING, REMOVE THE WHOLE ELSE CLAUSE
        with open(os.path.join(os.path.split(__file__)[0], 'raket.jpg'),
                  'rb') as f:
            encoded_jpg = base64.b64encode(f.read())
            print(encoded_jpg)

    if encoded_jpg:
        msg = VOEG_ZAAK_DOCUMENT_TOE.format(**{
            'ZKN_UUID': escape(signal['signal_id']),
            'DOC_UUID': escape(str(uuid.uuid4())),
            'DATA': encoded_jpg.decode('utf-8'),
            'DOC_TYPE': 'JPG',
            'DOC_TYPE_LOWER': 'jpg',
            'FILE_NAME': 'MORA-' + escape(str(signal['id'])) + '.jpg'
        })
        return msg
    else:
        return ''


def _send_stuf_message(stuf_msg: str, soap_action: str):
    """
    Send a STUF message to the server that is configured.
    """
    if not settings.SIGMAX_AUTH_TOKEN or not settings.SIGMAX_SERVER:
        msg = 'SIGMAX_AUTH_TOKEN or SIGMAX_SERVER not configured.'
        raise ServiceNotConfigured(msg)

    # Prepare our request to Sigmax
    encoded = stuf_msg.encode('utf-8')
    headers = {
        'SOAPAction': soap_action,
        'Content-Type': 'text/xml; charset=UTF-8',
        'Authorization': 'Basic ' + settings.SIGMAX_AUTH_TOKEN,
        'Content-Length': bytes(len(encoded))
    }

    # Send our message to Sigmax
    response = requests.post(
        url=settings.SIGMAX_SERVER,
        headers=headers,
        data=encoded,
        verify=False
    )

    # We return the response object so that we can check the response from
    # the external API handler.
    return response


def handle_signal(signal: Signal):
    """Signal can be send to Sigmax at this point"""
    soap_action = CREEER_ZAAK_SOAPACTION
    msg = _generate_creeer_zaak_lk01_message(signal)
    response = _send_stuf_message(msg, soap_action)
    logger.info('Sent %s', soap_action)
    logger.info('Received:\n%s', response.text)

    soap_action = VOEG_ZAAKDOCUMENT_TOE_SOAPACTION
    msg = _generate_voeg_zaak_document_toe_lk01(signal)
    response = _send_stuf_message(msg, soap_action)
    logger.info('Sent %s', soap_action)
    logger.info('Received:\n%s', response.text)

    # Try to also send the image for this zaak
    soap_action = VOEG_ZAAKDOCUMENT_TOE_SOAPACTION
    msg = _generate_voeg_zaak_document_toe_lk01_jpg(signal)
    if msg:
        response = _send_stuf_message(msg, soap_action)
        logger.info('Sent %s', soap_action)
        logger.info('Received:\n%s', response.text)
    else:
        logger.info('No image, or URL expired for signal %s', signal.signal_id)


def is_signal_applicable(signal):
    """
    Determine is signal should be forwarded
    Todo: take history into account
    :param signal:
    :return: True when eligible
    """
    return signal.status.state == 'i' and signal.status.text.lower() == 'sigmax'
