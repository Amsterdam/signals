import base64
import os

from django.conf import settings
from django.contrib.staticfiles import finders
from django.utils import timezone
from django.views.generic.detail import SingleObjectMixin

from signals.apps.api.generics.permissions import SIAPermissions
from signals.apps.api.pdf.views import PDFTemplateView  # TODO: move these
from signals.apps.signals.models import Signal
from signals.auth.backend import JWTAuthBackend


def _get_data_uri(static_file):
    formats = {
        'svg': 'data:image/svg+xml;base64,',
        'jpg': 'data:image/jpeg;base64',
        'png': 'data:image/png;base64,',
    }

    result = finders.find(static_file)
    if result:
        filename = os.path.split(result)[1]
        ext = filename.split('.')[-1]

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
    pagination_class = None

    queryset = Signal.objects.all()

    template_name = 'api/pdf/print_signal.html'
    extra_context = {'now': timezone.datetime.now(), }

    def get_context_data(self, **kwargs):
        self.object = self.get_object()
        rd_coordinates = self.object.location.get_rd_coordinates()
        bbox = '{},{},{},{}'.format(
            rd_coordinates.x - 340.00,
            rd_coordinates.y - 125.00,
            rd_coordinates.x + 340.00,
            rd_coordinates.y + 125.00,
        )

        logo_src = _get_data_uri(settings.API_PDF_LOGO_STATIC_FILE)

        return super(GeneratePdfView, self).get_context_data(
            bbox=bbox,
            images=self.object.attachments.filter(is_image=True),
            user=self.request.user,
            logo_src=logo_src,
        )
