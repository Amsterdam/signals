"""
This module contains the PDF generation code used for Sigmax.
"""
import base64
import logging
from io import BytesIO

import requests
import weasyprint
from django.template.loader import render_to_string
from django.utils import timezone
from PIL import Image
from requests.exceptions import RequestException

from signals.apps.signals.models import Attachment, Signal

# Because weasyprint can produce a lot of warnings (unsupported
# CSS etc.) we ignore them.
logging.getLogger('weasyprint').setLevel(100)
logger = logging.getLogger(__name__)


def _get_jpg_data_url(attachment: Attachment):
    """
    Download image, resize it, base 64 encode it, and finally create a image data URL from it.
    """
    # HOTFIX for SIG-1473
    # - Weazyprint JPG support assumes GDK Bixbuf - https://github.com/Kozea/WeasyPrint/issues/428)
    # - long term solution must use a image resizing micro-service

    MAX_SIZE = 800  # width and height no larger than this value

    try:
        data = BytesIO(requests.get(attachment.file.url).content)  # try/except network stuff
    except RequestException:
        logger.warning('Could not access: {} for resizing.'.format(attachment.file.url))
        return None

    image = Image.open(data)

    # Consider image orientation:
    if image.width > image.height:
        # landscape
        width = MAX_SIZE
        height = int((MAX_SIZE / image.width) * image.height)
    else:
        # portrait
        width = int((MAX_SIZE / image.height) * image.width)
        height = MAX_SIZE

    resized = image.resize(size=(width, height), resample=Image.LANCZOS).convert('RGB')

    buffer = BytesIO()
    resized.save(buffer, format='JPEG')

    return 'data:image/jpg;base64,' + base64.b64encode(buffer.getvalue()).decode('utf-8')


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
    # HOTFIX for SIG-1473
    jpg_data_urls = []
    for attachment in signal.attachments.all():
        data_url = _get_jpg_data_url(attachment)
        jpg_data_urls.append(data_url)
        assert data_url is None or data_url.startswith('data:image/jpg')

    context = {
        'signal': signal,
        'now': timezone.datetime.now(),
        'bbox': bbox,
        'user': None,
        'jpg_data_urls': jpg_data_urls,
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
