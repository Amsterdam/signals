# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
import base64
import io
import logging
import os

import weasyprint
from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.exceptions import SuspiciousFileOperation
from django.template.loader import render_to_string
from django.utils import timezone

from signals.apps.services.domain.images import DataUriImageEncodeService
from signals.apps.signals.utils.map import MapGenerator

logger = logging.getLogger(__name__)


def _get_data_uri(static_file):
    formats = {
        '.svg': 'data:image/svg+xml;base64,',
        '.jpg': 'data:image/jpeg;base64',
        '.png': 'data:image/png;base64,',
    }

    if not static_file:  # protect against None or ''
        return ''

    try:
        result = finders.find(static_file)
    except SuspiciousFileOperation:  # when file path starts with /
        return ''

    if result:
        _, ext = os.path.splitext(result)
        if not ext:
            return ''

        try:
            start = formats[ext]
        except KeyError:
            return ''  # We want no HTTP 500, just a missing image

        with open(result, 'rb') as f:
            encoded = base64.b64encode(f.read()).decode('utf-8')
        data_uri = start + encoded

        return data_uri
    else:
        return ''  # missing static file, results in missing image


class PDFSummaryService:
    max_size = settings.API_PDF_RESIZE_IMAGES_TO

    @staticmethod
    def _get_context_data(signal, user):
        logo_src = _get_data_uri(settings.API_PDF_LOGO_STATIC_FILE)
        img_data_uri = None
        bbox = None

        map_generator = MapGenerator()

        if settings.DEFAULT_MAP_TILE_SERVER:
            map_img = map_generator.make_map(
                url_template=settings.DEFAULT_MAP_TILE_SERVER,
                lat=signal.location.geometrie.coords[1],
                lon=signal.location.geometrie.coords[0],
                zoom=17,
                img_size=[680, 250]
            )
            # transform image to png -> bytes -> data uri
            png_array = io.BytesIO()
            map_img.save(png_array, format='png')
            encoded = base64.b64encode(png_array.getvalue()).decode()
            img_data_uri = 'data:image/png;base64,{}'.format(encoded)
        else:
            rd_coordinates = signal.location.get_rd_coordinates()
            bbox = '{},{},{},{}'.format(
                rd_coordinates.x - 340.00,
                rd_coordinates.y - 125.00,
                rd_coordinates.x + 340.00,
                rd_coordinates.y + 125.00,
            )
        jpg_data_uris, att_filenames, user_emails, att_created_ats = \
            DataUriImageEncodeService.get_context_data_images(signal, PDFSummaryService.max_size)

        return {
            'signal': signal,
            'bbox': bbox,
            'img_data_uri': img_data_uri,
            'attachment_images': zip(jpg_data_uris, att_filenames, user_emails, att_created_ats),
            'user': user,
            'logo_src': logo_src,
            'now': timezone.now(),
        }

    @staticmethod
    def _get_html(signal, user):
        context = PDFSummaryService._get_context_data(signal, user)
        return render_to_string('api/pdf/print_signal.html', context=context)

    @staticmethod
    def get_pdf(signal, user):
        html = PDFSummaryService._get_html(signal, user)
        return weasyprint.HTML(string=html).write_pdf()
