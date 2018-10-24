from signals import API_VERSIONS
from signals.utils.version import get_version


class APIVersionHeaderMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Checking if we're coming from a DRF view, which contains API versioning information.
        # If so, add a HTTP header with API version number.
        renderer_context = getattr(response, 'renderer_context', {})
        drf_request = renderer_context.get('request', None)
        if drf_request and getattr(drf_request, 'version', None):
            response['X-API-Version'] = get_version(API_VERSIONS[drf_request.version])

        return response
