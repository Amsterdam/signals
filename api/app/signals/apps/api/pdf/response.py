# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from django.template.response import TemplateResponse

from signals.apps.services.domain.pdf_summary import PDFSummaryService


class PDFTemplateResponse(TemplateResponse):
    def __init__(self, filename=None, attachment=True, *args, **kwargs):
        self._content_type = kwargs.get('content_type')
        super().__init__(*args, **kwargs)
        if filename:
            self['Content-Disposition'] = '{}filename="{}"'.format(
                'attachment;' if attachment else 'inline;',
                filename,
            )

    @property
    def rendered_content(self):
        return PDFSummaryService.get_pdf(self.context_data['signal'], self.context_data['user'])
