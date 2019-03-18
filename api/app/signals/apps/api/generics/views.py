import os

from django.views.generic.base import TemplateView


class SwaggerView(TemplateView):
    template_name = 'api/swagger/openapi.yaml'

    def get_context_data(self, **kwargs):
        global_api_root = os.getenv('global_api_root', None)

        context = super().get_context_data(**kwargs)
        context['global_api_root'] = global_api_root
        return context
