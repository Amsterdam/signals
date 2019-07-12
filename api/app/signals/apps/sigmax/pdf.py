"""
This module contains the PDF generation code used for Sigmax.
"""
import base64
import logging

import weasyprint
from django.template.loader import render_to_string
from django.utils import timezone

from signals.apps.signals.models import Signal

# Because weasyprint can produce a lot of warnings (unsupported
# CSS etc.) we ignore them.
logging.getLogger('weasyprint').setLevel(100)


def _render_html(signal: Signal):
    """Render given `Signal` with HTML template used for PDF generation.

    :param signal: Signal object
    :returns: HTML str
    """
    rd_coordinates = signal.location.get_rd_coordinates()
    bbox = '{},{},{},{}'.format(
        rd_coordinates.x - 340.00,
        rd_coordinates.y - 125.00,
        rd_coordinates.x + 340.00,
        rd_coordinates.y + 125.00,
    )
    context = {
        'signal': signal,
        'now': timezone.datetime.now(),
        'bbox': bbox,
        'images': signal.attachments.filter(is_image=True),
        'user': None,
    }
    return render_to_string('api/pdf/print_signal.html', context=context)


def _generate_pdf(signal: Signal):
    """Generate PDF to send to VoegZaakdocumentToe_Lk01.

    :param signal: Signal object
    :returns: base64 encoded data
    """
    html = _render_html(signal)
    pdf = weasyprint.HTML(string=html).write_pdf()

    return base64.b64encode(pdf)
