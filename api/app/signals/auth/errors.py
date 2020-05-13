from django import http


class AuthzConfigurationError(Exception):
    """ Error for missing / invalid configuration"""


class AuthorizationHeaderError(Exception):
    def __init__(self, response):
        self.response = response


def invalid_request():
    msg = (
        "Bearer realm=\"Signals\", error=\"invalid_request\", "
        "error_description=\"Invalid Authorization header format; "
        "should be: 'Bearer [token]'\"")
    response = http.HttpResponse('Bad Request', status=400)
    response['WWW-Authenticate'] = msg
    return response
