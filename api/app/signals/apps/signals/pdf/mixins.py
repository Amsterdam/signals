import weasyprint
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.generic.base import TemplateResponseMixin


class PDFTemplateResponseMixin(TemplateResponseMixin):
    pdf_filename = None

    def get_pdf_filename(self):
        return self.pdf_filename

    def get_pdf_response(self, context, **response_kwargs):
        html = render_to_string(self.get_template_names(), context=context)
        content = weasyprint.HTML(string=html).write_pdf()

        response = HttpResponse(content, content_type='application/pdf')
        filename = self.get_pdf_filename()
        if filename is not None:
            response['Content-Disposition'] = 'attachment; {}'.format(filename)
        return response

    def render_to_response(self, context, **response_kwargs):
        return self.get_pdf_response(context, **response_kwargs)
