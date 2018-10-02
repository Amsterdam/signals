from rest_framework.throttling import BaseThrottle


def get_ip(request):
    """Get IP address from given request.

    :param request: Request object
    :returns: str or None
    """
    if request and hasattr(request, 'get_token_subject'):
        return BaseThrottle().get_ident(request)
    return None
