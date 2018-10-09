"""
This module contains the PDF generation code used for Sigmax.
"""
import base64
import logging

import weasyprint
from django.conf import settings
from django.contrib.sites.models import Site
from django.template.loader import render_to_string
from swift.storage import SwiftStorage

# Because weasyprint can produce a lot of warnings (unsupported
# CSS etc.) we ignore them.
from signals.apps.signals.models import Signal

logging.getLogger('weasyprint').setLevel(100)


def _render_html(signal: Signal):
    context = {'signal': signal, }
    if signal.image:
        is_swift = isinstance(signal.image.storage, SwiftStorage)
        if is_swift:
            context['image_url'] = signal.image.url  # Generated temp url to Swift Object Store.
        else:
            # Generating a fully qualified url ourself.
            current_site = Site.objects.get_current()
            local = 'localhost' in current_site.domain or settings.DEBUG
            context['image_url'] = '{scheme}://{domain}/{path}'.format(
                scheme='http' if local else 'https',
                domain=current_site.domain,
                path=signal.image.url)

    return render_to_string('sigmax/pdf_template.html', context=context)


def _generate_pdf(signal: Signal):
    """
    Generate PDF to send to VoegZaakdocumentToe_Lk01 (returns base64 encoded data).
    """
    html = _render_html(signal)
    pdf = weasyprint.HTML(string=html).write_pdf()

    return base64.b64encode(pdf)
