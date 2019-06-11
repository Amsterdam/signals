from django.views.generic.base import TemplateResponseMixin

from signals.apps.api.pdf.response import PDFTemplateResponse


class PDFTemplateResponseMixin(TemplateResponseMixin):
    response_class = PDFTemplateResponse
    pdf_filename = None
    content_type = 'application/pdf'

    def get_pdf_filename(self):
        if not self.pdf_filename:
            self.pdf_filename = 'SIA-{}.pdf'.format(self.object.pk)
        return self.pdf_filename

    def render_to_response(self, context, **response_kwargs):
        response_kwargs.update({
            'filename': self.get_pdf_filename(),
        })
        return super(PDFTemplateResponseMixin, self).render_to_response(context=context,
                                                                        **response_kwargs)
