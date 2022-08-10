# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2022 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
import base64
import io
import logging
import os
from urllib.parse import urlparse

import requests
import weasyprint
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.staticfiles import finders
from django.core.exceptions import SuspiciousFileOperation
from django.template.loader import render_to_string
from django.utils import timezone

from signals.apps.services.domain.images import DataUriImageEncodeService
from signals.apps.services.domain.wmts_map_generator import WMTSMapGenerator

logger = logging.getLogger(__name__)


class PDFSummaryService:
    max_size = settings.API_PDF_RESIZE_IMAGES_TO
    logo_formats = {
        '.svg': 'data:image/svg+xml;base64,',
        '.jpg': 'data:image/jpeg;base64',
        '.png': 'data:image/png;base64,',
    }

    @staticmethod
    def _get_logo_data_from_static_file(logo_url):
        """
        Retrieve static file, base64 encode it.
        """
        try:
            result = finders.find(logo_url)
        except SuspiciousFileOperation:  # when file path starts with /
            return ''

        if not result:
            return ''

        with open(result, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')

    @staticmethod
    def _get_logo_data_from_remote_url(logo_url):
        """
        Download external file, base64 encode it.
        """
        response = requests.get(logo_url)
        try:
            response.raise_for_status()
        except requests.HTTPError:
            return ''

        return base64.b64encode(response.content).decode('utf-8')

    @staticmethod
    def _get_logo_data(logo_url):
        """
        Get base64 encoded image data for logo.

        Note: path without scheme is assumed to be a static file reference and
        path with scheme is considered an external URL.
        """
        if not logo_url:  # protect against None or ''
            return ''

        # Check whether we have one of the allowable filetypes specified
        parsed = urlparse(logo_url, scheme='')
        _, ext = os.path.splitext(parsed.path)
        try:
            start = PDFSummaryService.logo_formats[ext]
        except KeyError:
            return ''  # We want no HTTP 500, just a missing image

        # Retrieve the base64 encoded image data
        data = ''
        if not parsed.scheme:
            data = PDFSummaryService._get_logo_data_from_static_file(logo_url)
        elif parsed.scheme in ('https', 'http'):
            data = PDFSummaryService._get_logo_data_from_remote_url(logo_url)

        if data:
            return start + data
        return ''

    @staticmethod
    def _get_contact_details(signal, user, include_contact_details):
        """
        Get reporter email and phone, redacted if needed.

        Note: contact details are redacted if the requesting user does not have
        "signals.sia_can_view_contact_details" and the override is not used.
        The override `include_contact_details` is used when a PDF generation is
        not triggered by a user but the contact details are needed. If no
        email or phone number is known it must not be redacted.
        """
        # Note: CityControl/Sigmax uses the `include_contact_details` override.
        if user and user.has_perm('signals.sia_can_view_contact_details') or include_contact_details:
            return signal.reporter.email, signal.reporter.phone

        return '*****' if signal.reporter.email else None, '*****' if signal.reporter.phone else None

    @staticmethod
    def _get_map_data(signal):
        """
        Get context data for map in PDF.
        """
        img_data_uri = None
        bbox = None

        if settings.DEFAULT_MAP_TILE_SERVER:
            # This flow is meant for WMTS services.
            map_img = WMTSMapGenerator.make_map(
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
            # This flow is meant for WMS services that serve data in EPSG:28992
            # (Rijksdriehoek) coordinate system (continental Netherlands).
            rd_coordinates = signal.location.get_rd_coordinates()
            bbox = '{},{},{},{}'.format(
                rd_coordinates.x - 340.00,
                rd_coordinates.y - 125.00,
                rd_coordinates.x + 340.00,
                rd_coordinates.y + 125.00,
            )
        return bbox, img_data_uri

    @staticmethod
    def _get_context_data(signal, user, include_contact_details):
        """
        Context data for the PDF HTML template.
        """
        logo_src = PDFSummaryService._get_logo_data(settings.API_PDF_LOGO_STATIC_FILE)

        bbox, img_data_uri = PDFSummaryService._get_map_data(signal)
        jpg_data_uris, att_filenames, user_emails, att_created_ats = \
            DataUriImageEncodeService.get_context_data_images(signal, PDFSummaryService.max_size)
        reporter_email, reporter_phone = PDFSummaryService._get_contact_details(signal, user, include_contact_details)

        return {
            'signal': signal,
            'bbox': bbox,
            'img_data_uri': img_data_uri,
            'attachment_images': zip(jpg_data_uris, att_filenames, user_emails, att_created_ats),
            'user': user if user else AnonymousUser(),
            'logo_src': logo_src,
            'now': timezone.now(),
            'reporter_email': reporter_email,
            'reporter_phone': reporter_phone,
            'FEATURE_FLAGS': settings.FEATURE_FLAGS
        }

    @staticmethod
    def _get_html(signal, user, include_contact_details):
        """
        Render PDF HTML template.
        """
        context = PDFSummaryService._get_context_data(signal, user, include_contact_details)
        return render_to_string('api/pdf/print_signal.html', context=context)

    @staticmethod
    def get_pdf(signal, user, include_contact_details=False):
        """
        Get PDF summary for a given signal.
        """
        html = PDFSummaryService._get_html(signal, user, include_contact_details)
        return weasyprint.HTML(string=html).write_pdf()
