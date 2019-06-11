import weasyprint
from django.template.response import TemplateResponse


class PDFTemplateResponse(TemplateResponse):
    def __init__(self, filename=None, attachment=True, *args, **kwargs):
        self._content_type = kwargs.get('content_type')
        super(PDFTemplateResponse, self).__init__(*args, **kwargs)
        if filename:
            self['Content-Disposition'] = '{}filename="{}"'.format(
                'attachment;' if attachment else 'inline;',
                filename,
            )

    @property
    def rendered_content(self):
        html = weasyprint.HTML(string=super(PDFTemplateResponse, self).rendered_content)
        return html.write_pdf()
