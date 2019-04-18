from django.views.generic.base import ContextMixin
from rest_framework.generics import GenericAPIView

from signals.apps.api.pdf.mixins import PDFTemplateResponseMixin


class PDFTemplateView(PDFTemplateResponseMixin, ContextMixin, GenericAPIView):
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)
