from django.urls import reverse
from rest_framework import routers

from signals import API_VERSIONS
from signals.utils.version import get_version


class SignalsAPIRootViewVersion0(routers.APIRootView):
    """
    List Signals and their related information.

    These API endpoints are part of the Signalen Informatievoorziening Amsterdam
    (SIA) application. SIA can be used by citizens and interested parties to inform
    the Amsterdam municipality of problems in public spaces (like noise complaints,
    broken street lights etc.) These signals (signalen in Dutch) are then followed
    up on by the appropriate municipal services.

    The code for this application (and associated web front-end) is available from:
    - https://github.com/Amsterdam/signals
    - https://github.com/Amsterdam/signals-frontend

    Note:
    Most of these endpoints require authentication. The only fully public endpoint
    is /signals/signal where new signals can be POSTed.
    """

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
        return 'Signals API Version 0'


class SignalsRouterVersion0(routers.DefaultRouter):
    APIRootView = SignalsAPIRootViewVersion0
