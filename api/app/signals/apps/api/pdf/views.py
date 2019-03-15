from django.views.generic.base import ContextMixin, View

from signals.apps.signals.pdf.mixins import PDFTemplateResponseMixin


class PDFTemplateView(PDFTemplateResponseMixin, ContextMixin, View):
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)
