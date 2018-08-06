"""
This module contains the PDF generation code used for Sigmax.
"""
import os
import logging
import base64
import warnings


import weasyprint
from dateutil.parser import parse

from django.template.loader import render_to_string

# Because weasyprint can produce a lot of warnings (unsupported
# CSS etc.) we ignore them.
from signals.models import Signal

logging.getLogger('weasyprint').setLevel(100)


def _render_html(signal: Signal):
    dt = parse(signal['created_at'])

    return render_to_string('pdf_template.html', context={
        'signal': signal,
        'datum': dt.strftime('%Y %m %d'),
        'tijdstip': dt.strftime('%H:%M:%S'),
        'hoofdrubriek': signal.category.main,
        'subrubriek': signal.category.sub,
        'omschrijving': signal['text'],
        'stadsdeel': '',  # TODO, extract from gebieden API?
        'adres': signal['location']['address_text'],
        'bron': signal['source'],
        'email': 'placeholder@example.com',
        'telefoonnummer': 'nvt',
    })


def _generate_pdf(signal):
    """
    Generate PDF to send to VoegZaakdocumentToe_Lk01 (returns base64 encoded data).
    """
    html = _render_html(signal)
    pdf = weasyprint.HTML(string=html).write_pdf()

    return base64.b64encode(pdf)
