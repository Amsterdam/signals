# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2021 Gemeente Amsterdam
"""
This module contains the PDF generation code used for Sigmax.
"""
import base64
import logging

from signals.apps.services.domain.pdf_summary import PDFSummaryService
from signals.apps.signals.models import Signal

# Because weasyprint can produce a lot of warnings (unsupported
# CSS etc.) we ignore them.
logging.getLogger('weasyprint').setLevel(100)
logger = logging.getLogger(__name__)


def _generate_pdf(signal: Signal):
    """Generate PDF to send to VoegZaakdocumentToe_Lk01.

    :param signal: Signal object
    :returns: base64 encoded data
    """
    pdf = PDFSummaryService.get_pdf(signal, None)
    return base64.b64encode(pdf)
