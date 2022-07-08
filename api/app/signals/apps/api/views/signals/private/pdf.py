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
        return {
            'signal': self.object,
            'user': self.request.user
        }
