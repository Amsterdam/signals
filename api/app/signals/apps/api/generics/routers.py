from django.urls import reverse
from rest_framework import routers

from signals import API_VERSIONS
from signals.utils.version import get_version


class BaseSignalsAPIRootView(routers.APIRootView):
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        # Appending the index view with API version 1 information. For now we need to mix this with
        # the API version 0 index view.
        response.data['v1'] = {
            '_links': {
                'self': {
                    'href': request._request.build_absolute_uri(reverse('v1:api-root')),
                }
            },
            'version': get_version(API_VERSIONS['v1']),
            'status': 'in development',
        }
        return response

    def get_view_name(self):
        return 'Signals API'


class BaseSignalsRouter(routers.DefaultRouter):
    APIRootView = BaseSignalsAPIRootView
