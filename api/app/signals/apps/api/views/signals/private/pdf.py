# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2022 Gemeente Amsterdam
import base64
import io
import logging
import os

from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.exceptions import SuspiciousFileOperation
from django.utils import timezone
from django.views.generic.detail import SingleObjectMixin

from signals.apps.api.generics.permissions import SIAPermissions, SignalViewObjectPermission
from signals.apps.api.pdf.views import PDFTemplateView  # TODO: move these
from signals.apps.services.domain.images import DataUriImageEncodeService
from signals.apps.signals.models import Signal
from signals.apps.signals.utils.map import MapGenerator
from signals.auth.backend import JWTAuthBackend

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


class GeneratePdfView(SingleObjectMixin, PDFTemplateView):
    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SIAPermissions,)
    object_permission_classes = (SignalViewObjectPermission, )
    pagination_class = None
    map_generator = MapGenerator()

    queryset = Signal.objects.all()

    template_name = 'api/pdf/print_signal.html'
    extra_context = {'now': timezone.datetime.now(), }

    max_size = settings.API_PDF_RESIZE_IMAGES_TO

    def check_object_permissions(self, request, obj):
        for permission_class in self.object_permission_classes:
            permission = permission_class()
            if not permission.has_object_permission(request, self, obj):
                self.permission_denied(
                    request, message=getattr(permission, 'message', None)
                )

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        self.check_object_permissions(request=self.request, obj=obj)
        return obj

    def get_context_data(self, **kwargs):
        self.object = self.get_object()
        logo_src = _get_data_uri(settings.API_PDF_LOGO_STATIC_FILE)
        img_data_uri = None
        bbox = None

        if settings.DEFAULT_MAP_TILE_SERVER:
            map_img = self.map_generator.make_map(
                url_template=settings.DEFAULT_MAP_TILE_SERVER,
                lat=self.object.location.geometrie.coords[1],
                lon=self.object.location.geometrie.coords[0],
                zoom=17,
                img_size=[680, 250]
            )
            # transform image to png -> bytes -> data uri
            png_array = io.BytesIO()
            map_img.save(png_array, format='png')
            encoded = base64.b64encode(png_array.getvalue()).decode()
            img_data_uri = 'data:image/png;base64,{}'.format(encoded)
        else:
            rd_coordinates = self.object.location.get_rd_coordinates()
            bbox = '{},{},{},{}'.format(
                rd_coordinates.x - 340.00,
                rd_coordinates.y - 125.00,
                rd_coordinates.x + 340.00,
                rd_coordinates.y + 125.00,
            )
        jpg_data_uris, att_filenames, user_emails, att_created_ats = \
            DataUriImageEncodeService.get_context_data_images(self.object, self.max_size)

        return super().get_context_data(
            bbox=bbox,
            img_data_uri=img_data_uri,
            attachment_images=zip(jpg_data_uris, att_filenames, user_emails, att_created_ats),
            user=self.request.user,
            logo_src=logo_src,
        )
