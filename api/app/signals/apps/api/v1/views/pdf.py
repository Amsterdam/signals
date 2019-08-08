from django.utils import timezone
from django.views.generic.detail import SingleObjectMixin

from signals.apps.api.generics.permissions import SIAPermissions
from signals.apps.api.pdf.views import PDFTemplateView  # TODO: move these
from signals.apps.signals.models import Signal
from signals.auth.backend import JWTAuthBackend


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
        return super(GeneratePdfView, self).get_context_data(
            bbox=bbox,
            images=self.object.attachments.filter(is_image=True),
            user=self.request.user,
        )
