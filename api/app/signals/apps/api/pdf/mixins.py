import io

import weasyprint
from django.http import FileResponse
from django.template.loader import render_to_string
from django.views.generic.base import TemplateResponseMixin


class PDFTemplateResponseMixin(TemplateResponseMixin):
    pdf_filename = None

    def get_pdf_filename(self):
        if not self.pdf_filename:
            self.pdf_filename = 'SIA-{}.pdf'.format(self.object.pk)
        return self.pdf_filename

    def get_pdf_response(self, context, **response_kwargs):
        html = render_to_string(self.get_template_names(), context=context)
        buffer = io.BytesIO(weasyprint.HTML(string=html).write_pdf())

        return FileResponse(buffer, as_attachment=True, filename=self.get_pdf_filename())

    def render_to_response(self, context, **response_kwargs):
        return self.get_pdf_response(context, **response_kwargs)
