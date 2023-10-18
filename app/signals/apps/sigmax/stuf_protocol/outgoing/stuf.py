# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2023 Gemeente Amsterdam
import requests
from django.conf import settings
from lxml import etree
from requests import Response

from signals.apps.sigmax.stuf_protocol.exceptions import SigmaxException


def _stuf_response_ok(response: Response) -> bool:
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

    if not isinstance(found, list) or len(found) != 1:
        return False

    if not isinstance(found[0], etree._Element) or found[0].text != 'Bv03':
        return False

    return True


def _send_stuf_message(stuf_msg: str, soap_action: str) -> Response:
    """
    Send a STUF message to the server that is configured.
    """
    if not settings.SIGMAX_AUTH_TOKEN or not settings.SIGMAX_SERVER:
        raise SigmaxException('SIGMAX_AUTH_TOKEN or SIGMAX_SERVER not configured.')

    # Prepare our request to Sigmax
    encoded = stuf_msg.encode('utf-8')

    headers: dict[str, str | bytes] = {
        'SOAPAction': soap_action,
        'Content-Type': 'text/xml; charset=UTF-8',
        'Authorization': 'Basic ' + settings.SIGMAX_AUTH_TOKEN,
        'Content-Length': b'%d' % len(encoded)
    }

    cert = None
    if settings.SIGMAX_CLIENT_CERT and settings.SIGMAX_CLIENT_KEY:
        cert = (settings.SIGMAX_CLIENT_CERT, settings.SIGMAX_CLIENT_KEY)

    verify: bool | str = True
    if settings.SIGMAX_CA_BUNDLE:
        verify = settings.SIGMAX_CA_BUNDLE

    # Send our message to Sigmax. Network problems, and HTTP status codes
    # are all raised as errors.
    try:
        response = requests.post(
            url=settings.SIGMAX_SERVER,
            cert=cert,
            verify=verify,
            headers=headers,
            data=encoded,
            timeout=30,
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
