# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2022 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
"""
Support for voegZaakdocumentToe_Lk01 messages to send to CityControl.

Note: currently only used to send PDF documents to CityControl
"""
import base64
import logging
import uuid

from django.template.loader import render_to_string

from signals.apps.services.domain.pdf import PDFSummaryService
from signals.apps.sigmax.stuf_protocol.outgoing.creeerZaak_Lk01 import _send_stuf_message

logger = logging.getLogger(__name__)


VOEG_ZAAKDOCUMENT_TOE = '"http://www.egem.nl/StUF/sector/zkn/0310/VoegZaakdocumentToe_Lk01"'


def _generate_voegZaakdocumentToe_Lk01(signal, seq_no):
    """
    Generate XML for Sigmax voegZaakdocumentToe_Lk01 (for the PDF case)
    """
    pdf = PDFSummaryService.get_pdf(signal, None, True)
    encoded_pdf = base64.b64encode(pdf)

    return render_to_string('sigmax/voegZaakdocumentToe_Lk01.xml', context={
        'signal': signal,
        'sequence_number': seq_no,
        'DOC_UUID': str(uuid.uuid4()),
        'DATA': encoded_pdf.decode('utf-8'),
        'DOC_TYPE': 'PDF',
        'FILE_NAME': f'{signal.get_id_display()}.pdf'
    })


def send_voegZaakdocumentToe_Lk01(signal, seq_no):
    soap_action = VOEG_ZAAKDOCUMENT_TOE
    msg = _generate_voegZaakdocumentToe_Lk01(signal, seq_no)
    response = _send_stuf_message(msg, soap_action)

    logger.info('Sent %s', soap_action)
    logger.info('Received:\n%s', response.text)
    return response
